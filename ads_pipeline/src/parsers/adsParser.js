const { extractImpressionRange } = require('../utils/impression');
const { extractVideoUrlsFromObject } = require('../utils/video');

function walk(node, visit, depth = 0) {
  visit(node, depth);

  if (Array.isArray(node)) {
    node.forEach((item) => walk(item, visit, depth + 1));
    return;
  }

  if (node && typeof node === 'object') {
    Object.values(node).forEach((value) => walk(value, visit, depth + 1));
  }
}

function findBestImpression(node) {
  if (!node || typeof node !== 'object') return null;

  let best = null;

  walk(node, (value) => {
    if (typeof value !== 'string' || !/impression/i.test(value)) return;

    const parsed = extractImpressionRange(value);
    if (!parsed) return;

    if (!best || parsed.score > best.score) {
      best = parsed;
    }
  });

  return best;
}

function collectStrings(node, out = []) {
  if (typeof node === 'string') {
    out.push(node);
    return out;
  }

  if (Array.isArray(node)) {
    node.forEach((item) => collectStrings(item, out));
    return out;
  }

  if (node && typeof node === 'object') {
    Object.values(node).forEach((value) => collectStrings(value, out));
  }

  return out;
}

function findValueByKeyMatcher(node, matcher) {
  let result;

  walk(node, (value) => {
    if (result !== undefined) return;
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;

    Object.entries(value).forEach(([key, fieldValue]) => {
      if (result !== undefined) return;
      if (!matcher(key, fieldValue)) return;
      result = fieldValue;
    });
  });

  return result;
}

function toDisplayDate(value) {
  if (value === null || value === undefined) return null;

  let date;

  if (typeof value === 'number') {
    const normalizedTs = value > 9_999_999_999 ? value : value * 1000;
    date = new Date(normalizedTs);
  } else if (typeof value === 'string') {
    date = new Date(value);
  }

  if (!date || Number.isNaN(date.getTime())) return null;

  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
}

function extractLibraryId(node, strings) {
  const directValue = findValueByKeyMatcher(node, (key, value) => {
    if (value === null || value === undefined) return false;
    const normalizedKey = key.toLowerCase();

    const isMatch =
      normalizedKey === 'ad_archive_id' ||
      normalizedKey === 'library_id' ||
      normalizedKey === 'archive_id' ||
      normalizedKey.includes('library_id') ||
      normalizedKey.includes('archive_id');

    if (!isMatch) return false;

    const strValue = String(value);
    return /^\d{8,}$/.test(strValue);
  });

  if (directValue) return String(directValue);

  for (const text of strings) {
    const match = text.match(/Library\s*ID\s*:\s*(\d{8,})/i);
    if (match) return match[1];
  }

  return null;
}

function extractLibraryIdFromAd(node) {
  let result = null;

  walk(node, (value) => {
    if (result) return;
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;

    Object.entries(value).forEach(([key, fieldValue]) => {
      if (result) return;
      
      const normalizedKey = key.toLowerCase();
      if (!normalizedKey.includes('id')) return;

      const strValue = String(fieldValue || '');
      if (/^\d{10,}$/.test(strValue)) {
        result = strValue;
      }
    });
  });

  return result;
}
function extractStatus(node, strings) {
  const activeStatus = findValueByKeyMatcher(node, (key, value) => {
    if (typeof value !== 'string') return false;
    return key.toLowerCase().includes('active_status');
  });

  if (typeof activeStatus === 'string') {
    return activeStatus.charAt(0).toUpperCase() + activeStatus.slice(1).toLowerCase();
  }

  const isActive = findValueByKeyMatcher(node, (key, value) => {
    if (typeof value !== 'boolean') return false;
    const normalized = key.toLowerCase();
    return normalized.includes('is_active') || normalized.includes('active');
  });

  if (typeof isActive === 'boolean') {
    return isActive ? 'Active' : 'Inactive';
  }

  for (const text of strings) {
    if (/\bactive\b/i.test(text)) return 'Active';
    if (/\binactive\b/i.test(text)) return 'Inactive';
  }

  return null;
}

function extractStartDate(node, strings) {
  const directDate = findValueByKeyMatcher(node, (key, value) => {
    if (typeof value !== 'string' && typeof value !== 'number') return false;
    const normalized = key.toLowerCase();

    return (
      normalized.includes('start_date') ||
      normalized.includes('start_time') ||
      normalized.includes('delivery_start') ||
      normalized.includes('ad_delivery_start')
    );
  });

  const parsedDirectDate = toDisplayDate(directDate);
  if (parsedDirectDate) return parsedDirectDate;

  for (const text of strings) {
    const match = text.match(/Started\s+running\s+on\s+([^\n]+)/i);
    if (match) return match[1].trim();
  }

  return null;
}

function normalizePlatformLabel(platform) {
  const normalized = String(platform).toLowerCase().replace(/[_\s]+/g, ' ').trim();

  const mapping = {
    facebook: 'Facebook',
    instagram: 'Instagram',
    messenger: 'Messenger',
    'audience network': 'Audience Network',
    threads: 'Threads',
    whatsapp: 'WhatsApp'
  };

  return mapping[normalized] || normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function extractPlatforms(node, strings) {
  const platformSet = new Set();

  walk(node, (value) => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return;

    Object.entries(value).forEach(([key, fieldValue]) => {
      if (!fieldValue) return;

      const normalizedKey = key.toLowerCase();
      if (!normalizedKey.includes('platform')) return;

      if (Array.isArray(fieldValue)) {
        fieldValue.forEach((item) => {
          if (typeof item === 'string') platformSet.add(normalizePlatformLabel(item));
        });
      } else if (typeof fieldValue === 'string') {
        platformSet.add(normalizePlatformLabel(fieldValue));
      }
    });
  });

  const platformRegex = /facebook|instagram|messenger|audience[_\s]?network|threads|whatsapp/gi;
  strings.forEach((text) => {
    const matches = text.match(platformRegex);
    if (!matches) return;
    matches.forEach((item) => platformSet.add(normalizePlatformLabel(item)));
  });

  return [...platformSet];
}

function extractAdMetadata(node) {
  const strings = collectStrings(node, []);

  return {
    status: extractStatus(node, strings),
    libraryId: extractLibraryId(node, strings),
    startedRunningOn: extractStartDate(node, strings),
    platforms: extractPlatforms(node, strings)
  };
}

function debugExtractedMetadata(entries) {
  if (!entries || !entries.length) return {};

  const withMetadata = entries.filter(e => 
    e.libraryId || e.status || e.startedRunningOn || (e.platforms && e.platforms.length)
  );

  const withoutMetadata = entries.filter(e => 
    !e.libraryId && !e.status && !e.startedRunningOn && (!e.platforms || !e.platforms.length)
  );

  return {
    total: entries.length,
    withMetadata: withMetadata.length,
    withoutMetadata: withoutMetadata.length,
    stats: {
      hasLibraryId: entries.filter(e => e.libraryId).length,
      hasStatus: entries.filter(e => e.status).length,
      hasStartDate: entries.filter(e => e.startedRunningOn).length,
      hasPlatforms: entries.filter(e => e.platforms && e.platforms.length).length
    }
  };
}

function extractVideoEntriesFromGraphQlPayload(payload) {
  const entries = [];
  let sourceOrder = 0;

  walk(payload, (node, depth) => {
    if (!node || typeof node !== 'object') return;
    if (depth < 2) return;

    const videoUrls = extractVideoUrlsFromObject(node);
    if (!videoUrls.length) return;

    const metadata = extractAdMetadata(node);
    const libraryId = metadata.libraryId || extractLibraryIdFromAd(node);
    if (!libraryId) return;

    const uniqueVideoUrls = [...new Set(videoUrls)];
    const primaryVideoUrl = uniqueVideoUrls[0];
    if (!primaryVideoUrl) return;

    const impression = findBestImpression(node);

    entries.push({
      videoUrl: primaryVideoUrl,
      impressionText: impression ? impression.text : null,
      impressionMin: impression ? impression.min : null,
      impressionMax: impression ? impression.max : null,
      impressionScore: impression ? impression.score : -1,
      status: metadata.status,
      libraryId,
      startedRunningOn: metadata.startedRunningOn,
      platforms: metadata.platforms,
      sourceOrder: sourceOrder++
    });
  });

  return entries;
}

module.exports = {
  extractVideoEntriesFromGraphQlPayload,
  debugExtractedMetadata
};
