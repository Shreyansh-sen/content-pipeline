const { chromium } = require('playwright');
const { getAdsLibraryUrl, SCRAPER_CONFIG } = require('../config/constants');
const { extractVideoEntriesFromGraphQlPayload, debugExtractedMetadata } = require('../parsers/adsParser');
const { extractFiltersFromAdsUrl } = require('../utils/adsUrl');

function getHttpMp4(value) {
  const url = String(value || '').trim();
  if (!/^https?:/i.test(url)) return '';
  if (!/\.mp4(\?|$)/i.test(url)) return '';
  return url;
}

function pickValue(primary, fallback) {
  if (primary === null || primary === undefined || primary === '') return fallback;
  return primary;
}

function mergePlatforms(existing = [], incoming = []) {
  return [...new Set([...(existing || []), ...(incoming || [])])];
}

function mergeEntry(existing, incoming) {
  if (!existing) {
    return {
      ...incoming,
      platforms: incoming.platforms || []
    };
  }

  const incomingScore = incoming.impressionScore || -1;
  const existingScore = existing.impressionScore || -1;
  const best = incomingScore > existingScore ? incoming : existing;
  const other = best === incoming ? existing : incoming;
  const sourceOrder = Math.min(
    Number.isFinite(existing.sourceOrder) ? existing.sourceOrder : Number.MAX_SAFE_INTEGER,
    Number.isFinite(incoming.sourceOrder) ? incoming.sourceOrder : Number.MAX_SAFE_INTEGER
  );

  return {
    ...best,
    status: pickValue(best.status, other.status),
    libraryId: pickValue(best.libraryId, other.libraryId),
    startedRunningOn: pickValue(best.startedRunningOn, other.startedRunningOn),
    impressionText: pickValue(best.impressionText, other.impressionText),
    impressionMin: pickValue(best.impressionMin, other.impressionMin),
    impressionMax: pickValue(best.impressionMax, other.impressionMax),
    platforms: mergePlatforms(best.platforms, other.platforms),
    sourceOrder
  };
}

function sortByRankThenImpression(a, b) {
  const orderA = Number.isFinite(a.sourceOrder) ? a.sourceOrder : Number.MAX_SAFE_INTEGER;
  const orderB = Number.isFinite(b.sourceOrder) ? b.sourceOrder : Number.MAX_SAFE_INTEGER;
  if (orderA !== orderB) return orderA - orderB;

  const scoreA = Number.isFinite(a.impressionScore) ? a.impressionScore : -1;
  const scoreB = Number.isFinite(b.impressionScore) ? b.impressionScore : -1;
  return scoreB - scoreA;
}

async function extractDomOrder(page) {
  return page.evaluate(() => {
    const normalize = (text) => String(text || '').replace(/\s+/g, ' ').trim();
    const entries = [];
    const seen = new Set();

    const nodes = [...document.querySelectorAll('div, span, p, a')];
    nodes.forEach((node) => {
      const text = normalize(node.textContent);
      const match = text.match(/Library\s*ID\s*[:#]?\s*(\d{8,})/i);
      if (!match) return;
      const id = match[1];
      if (seen.has(id)) return;
      seen.add(id);
      entries.push({ libraryId: id, domOrder: entries.length });
    });

    return entries;
  });
}

function buildOrderMaps(initialEntries = [], finalEntries = []) {
  const initialMap = new Map(initialEntries.map((x) => [x.libraryId, x.domOrder]));
  const finalMap = new Map(finalEntries.map((x) => [x.libraryId, x.domOrder]));

  return {
    initialMap,
    finalMap,
    initialCount: initialEntries.length
  };
}

async function waitForInitialCards(page, timeoutMs = 15000) {
  try {
    await page.waitForFunction(() => {
      const text = document.body ? document.body.innerText || '' : '';
      return /Library\s*ID\s*[:#]?\s*\d{8,}/i.test(text);
    }, { timeout: timeoutMs });
  } catch {
    // allow graceful fallback; scraper can still continue with network payloads
  }
}

function orderByDomIds(results, initialEntries = [], finalEntries = []) {
  const byId = new Map();
  const noId = [];

  results.forEach((item) => {
    if (item.libraryId) {
      if (!byId.has(item.libraryId)) byId.set(item.libraryId, item);
      return;
    }
    noId.push(item);
  });

  const ordered = [];
  const usedIds = new Set();

  const consume = (entries) => {
    entries.forEach((entry) => {
      const id = entry.libraryId;
      if (!id || usedIds.has(id)) return;
      const item = byId.get(id);
      if (!item) return;
      usedIds.add(id);
      ordered.push(item);
    });
  };

  // True top ads first (before any scroll)
  consume(initialEntries);
  // Then later loaded ads (after scroll)
  consume(finalEntries);

  // Then any remaining payload items not found in DOM snapshots
  byId.forEach((item, id) => {
    if (usedIds.has(id)) return;
    ordered.push(item);
  });

  // Finally items without library id
  return [...ordered, ...noId];
}

async function scrapeAdsVideos(options = {}) {
  const { filters = {}, adsLibraryUrl, ...restOptions } = options;

  const debugLog = {
    payloadsProcessed: 0,
    videosFound: 0,
    metadataStats: {},
    warnings: []
  };

  const derivedFilters = {
    ...extractFiltersFromAdsUrl(adsLibraryUrl || ''),
    ...filters
  };

  const config = {
    ...SCRAPER_CONFIG,
    ...restOptions
  };

  const browser = await chromium.launch({ headless: config.headless });
  const context = await browser.newContext();
  const page = await context.newPage();

  const byAdKey = new Map();
  const networkMp4s = [];
  const seenNetworkMp4 = new Set();

  page.on('response', async (response) => {
    try {
      const url = response.url();

      if (url.includes('graphql')) {
        const payload = await response.json();
        const entries = extractVideoEntriesFromGraphQlPayload(payload);
        debugLog.payloadsProcessed += 1;

        if (entries.length > 0) {
          debugLog.videosFound += entries.length;
          debugLog.metadataStats = debugExtractedMetadata(entries);
        }

        entries.forEach((entry) => {
          const key = entry.libraryId || entry.videoUrl;
          byAdKey.set(key, mergeEntry(byAdKey.get(key), entry));
        });
      }

      const mp4Url = getHttpMp4(url);
      if (mp4Url && !seenNetworkMp4.has(mp4Url)) {
        seenNetworkMp4.add(mp4Url);
        networkMp4s.push(mp4Url);
      }
    } catch {
      // ignore
    }
  });

  await page.goto(getAdsLibraryUrl(derivedFilters), { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(config.initialWaitMs);
  await waitForInitialCards(page, Math.max(8_000, config.initialWaitMs));

  // Snapshot top-of-feed order BEFORE scrolling so we keep true top ads first.
  const initialDomOrderEntries = await extractDomOrder(page);

  await page.evaluate(async ({ steps, delay }) => {
    for (let i = 0; i < steps; i++) {
      window.scrollBy(0, window.innerHeight);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }, { steps: config.scrollSteps, delay: config.scrollDelayMs });

  await page.waitForTimeout(config.finalWaitMs);

  const domOrderEntries = await extractDomOrder(page);
  const { initialMap, finalMap, initialCount } = buildOrderMaps(initialDomOrderEntries, domOrderEntries);

  let results = [...byAdKey.values()]
    .filter((item) => getHttpMp4(item.videoUrl))
    .map((item) => ({
      ...item,
      videoUrl: getHttpMp4(item.videoUrl),
      sourceOrder: initialMap.has(item.libraryId)
        ? initialMap.get(item.libraryId)
        : finalMap.has(item.libraryId)
          ? (initialCount + finalMap.get(item.libraryId))
          : (Number.isFinite(item.sourceOrder) ? (initialCount + item.sourceOrder) : Number.MAX_SAFE_INTEGER)
    }))
    .sort(sortByRankThenImpression);

  results = orderByDomIds(results, initialDomOrderEntries, domOrderEntries);

  if (!results.length && networkMp4s.length) {
    results = networkMp4s.map((videoUrl, index) => ({
      videoUrl,
      status: null,
      libraryId: null,
      startedRunningOn: null,
      platforms: [],
      impressionText: null,
      impressionMin: null,
      impressionMax: null,
      impressionScore: -1,
      sourceOrder: index
    }));
    debugLog.warnings.push('Using network mp4 fallback (metadata unavailable).');
  }

  debugLog.initialDomEntries = initialDomOrderEntries.length;
  debugLog.domEntries = domOrderEntries.length;
  debugLog.uniqueVideos = results.length;
  debugLog.networkMp4Captured = networkMp4s.length;
  debugLog.source = results.length && byAdKey.size ? 'graphql+dom-order' : 'network-fallback';

  await browser.close();
  return { results, debugLog };
}

module.exports = {
  scrapeAdsVideos
};
