const ADS_LIBRARY_BASE_URL = 'https://www.facebook.com/ads/library/';

const ADS_LIBRARY_FILTERS = {
  active_status: 'active',
  ad_type: 'all',
  country: 'IN',
  search_type: 'page',
  view_all_page_id: '160580977144612',
  is_targeted_country: 'false',
  media_type: 'all'
};

function buildAdsLibraryUrl(baseFilters = {}) {
  const filters = { ...ADS_LIBRARY_FILTERS, ...baseFilters };
  
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });

  params.append('sort_data[mode]', 'total_impressions');
  params.append('sort_data[direction]', 'desc');

  return `${ADS_LIBRARY_BASE_URL}?${params.toString()}`;
}

function getAdsLibraryUrl(overrides = {}) {
  return buildAdsLibraryUrl(overrides);
}

const SCRAPER_CONFIG = {
  headless: false,
  initialWaitMs: 5000,
  scrollSteps: 20,
  scrollDelayMs: 2500,
  finalWaitMs: 5000
};

module.exports = {
  ADS_LIBRARY_FILTERS,
  getAdsLibraryUrl,
  SCRAPER_CONFIG
};
