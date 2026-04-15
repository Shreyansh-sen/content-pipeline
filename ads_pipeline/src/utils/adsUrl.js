const { ADS_LIBRARY_FILTERS } = require('../config/constants');

const ALLOWED_FILTER_KEYS = Object.keys(ADS_LIBRARY_FILTERS);

function extractFiltersFromAdsUrl(inputUrl = '') {
  if (!inputUrl || typeof inputUrl !== 'string') {
    return {};
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(inputUrl);
  } catch (error) {
    throw new Error('Please enter a valid Facebook Ads Library URL.');
  }

  if (!/facebook\.com$/i.test(parsedUrl.hostname) && !/\.facebook\.com$/i.test(parsedUrl.hostname)) {
    throw new Error('Only Facebook Ads Library URLs are supported.');
  }

  const filters = {};

  ALLOWED_FILTER_KEYS.forEach((key) => {
    const value = parsedUrl.searchParams.get(key);
    if (value) filters[key] = value;
  });

  return filters;
}

module.exports = {
  extractFiltersFromAdsUrl
};
