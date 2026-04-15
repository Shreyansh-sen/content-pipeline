const https = require('https');
const http = require('http');
const { scrapeAdsVideos } = require('../services/adsScraperService');

async function scrapeFromUrl(req, res) {
  try {
    const inputUrl = (req.body?.url || '').trim();

    if (!inputUrl) {
      return res.status(400).json({
        ok: false,
        message: 'Please enter a Facebook Ads Library URL.'
      });
    }

    const videos = await scrapeAdsVideos({
      adsLibraryUrl: inputUrl,
      headless: true
    });

    const { results, debugLog } = videos;

    return res.json({
      ok: true,
      totalUniqueVideos: results.length,
      videos: results,
      debugLog
    });
  } catch (error) {
    return res.status(500).json({
      ok: false,
      message: error.message || 'Scraping failed. Please try again.'
    });
  }
}

function streamVideoDownload(req, res) {
  try {
    const videoUrl = (req.query?.url || '').trim();
    if (!videoUrl) {
      return res.status(400).json({ ok: false, message: 'Missing video URL.' });
    }

    let parsed;
    try {
      parsed = new URL(videoUrl);
    } catch (error) {
      return res.status(400).json({ ok: false, message: 'Invalid video URL.' });
    }

    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return res.status(400).json({ ok: false, message: 'Unsupported protocol.' });
    }

    const client = parsed.protocol === 'https:' ? https : http;
    const safeFileName = String(req.query?.filename || 'ad-video')
      .replace(/[^a-z0-9-_]/gi, '_')
      .replace(/_+/g, '_')
      .slice(0, 80);

    res.setHeader('Content-Disposition', `attachment; filename="${safeFileName || 'ad-video'}.mp4"`);

    client
      .get(parsed.toString(), (upstreamRes) => {
        const contentType = upstreamRes.headers['content-type'] || 'video/mp4';
        res.setHeader('Content-Type', contentType);
        upstreamRes.pipe(res);
      })
      .on('error', () => {
        if (!res.headersSent) {
          res.status(500).json({ ok: false, message: 'Unable to download video.' });
        } else {
          res.end();
        }
      });
  } catch (error) {
    return res.status(500).json({ ok: false, message: 'Unexpected download error.' });
  }
}

module.exports = {
  scrapeFromUrl,
  streamVideoDownload
};
