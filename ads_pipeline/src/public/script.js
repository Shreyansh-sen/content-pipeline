const form = document.getElementById('scrapeForm');
const submitBtn = document.getElementById('submitBtn');
const statusText = document.getElementById('statusText');
const summary = document.getElementById('summary');
const debugInfo = document.getElementById('debugInfo');
const results = document.getElementById('results');
const urlTab = document.getElementById('urlTab');
const filterTab = document.getElementById('filterTab');
const urlInput = document.getElementById('url-input');
const filterInput = document.getElementById('filter-input');
const adsUrlField = document.getElementById('adsUrl');
const libraryIdField = document.getElementById('libraryId');

// Tab switching
urlTab.addEventListener('click', () => switchTab('url-input', urlTab));
filterTab.addEventListener('click', () => switchTab('filter-input', filterTab));

function switchTab(tabName, tabBtn) {
  const allTabs = document.querySelectorAll('.tab-content');
  const allBtns = document.querySelectorAll('.tab-btn');

  allTabs.forEach((t) => t.classList.remove('active'));
  allBtns.forEach((b) => b.classList.remove('active'));

  document.getElementById(tabName).classList.add('active');
  tabBtn.classList.add('active');

  if (tabName === 'url-input') {
    adsUrlField.required = true;
    libraryIdField.required = false;
  } else {
    adsUrlField.required = false;
    libraryIdField.required = true;
  }
}

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? '#c02a2a' : '#566074';
}

function showDebug(message) {
  debugInfo.innerHTML = `<strong>Debug:</strong><br/>${message.replace(/</g, '&lt;').replace(/>/g, '&gt;')}`;
  debugInfo.classList.remove('hidden');
}

function getDownloadUrl(videoUrl, filename) {
  const params = new URLSearchParams({
    url: videoUrl,
    filename
  });

  return `/api/download?${params.toString()}`;
}

function createCard(video, index) {
  const card = document.createElement('article');
  card.className = 'video-card';

  const platforms = Array.isArray(video.platforms) && video.platforms.length
    ? video.platforms.join(', ')
    : 'N/A';

  const libraryId = video.libraryId || 'N/A';
  const started = video.startedRunningOn || 'N/A';
  const status = video.status || 'N/A';
  const impressions = video.impressionText || 'N/A';

  const fileName = `library_${libraryId}_${index + 1}`;

  card.innerHTML = `
    <video controls preload="metadata" src="${video.videoUrl}"></video>
    <div class="content">
      <h3 class="title">Video #${index + 1}</h3>
      <ul class="meta">
        <li><strong>Status:</strong> ${status}</li>
        <li><strong>Library ID:</strong> ${libraryId}</li>
        <li><strong>Started Running:</strong> ${started}</li>
        <li><strong>Platforms:</strong> ${platforms}</li>
        <li><strong>Impressions:</strong> ${impressions}</li>
      </ul>
      <div class="actions">
        <a class="download-btn" href="${getDownloadUrl(video.videoUrl, fileName)}">Download Video</a>
      </div>
    </div>
  `;

  return card;
}

function renderResults(videos) {
  results.innerHTML = '';

  videos.forEach((video, index) => {
    results.appendChild(createCard(video, index));
  });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  let url;
  const activeTab = document.querySelector('.tab-content.active');
  const isUrlMode = activeTab === urlInput;

  if (isUrlMode) {
    url = adsUrlField.value.trim();
    if (!url) {
      setStatus('Please enter a valid URL.', true);
      return;
    }
  } else {
    const libraryId = libraryIdField.value.trim();
    if (!libraryId) {
      setStatus('Please enter a Library/Page ID.', true);
      return;
    }

    const filters = {
      view_all_page_id: libraryId,
      country: document.getElementById('country').value || 'IN',
      ad_type: document.getElementById('mediaType').value || 'all',
      active_status: document.getElementById('activeStatus').value || 'active',
      search_type: 'page',
      is_targeted_country: 'false',
      media_type: 'all'
    };

    const lang = document.getElementById('language').value;
    if (lang) filters.language = lang;

    const platform = document.getElementById('platform').value;
    if (platform) filters.platform = platform;

    url = new URL('https://www.facebook.com/ads/library/');
    Object.entries(filters).forEach(([key, value]) => {
      if (value) url.searchParams.set(key, value);
    });
    
    url.searchParams.set('sort_data[mode]', 'total_impressions');
    url.searchParams.set('sort_data[direction]', 'desc');
    
    url = url.toString();
  }

  showDebug(`Built URL:<br/>${url}`);

  submitBtn.disabled = true;
  summary.classList.add('hidden');
  debugInfo.classList.add('hidden');
  results.innerHTML = '';
  setStatus('Fetching videos... this can take up to 1-2 minutes.');

  try {
    const response = await fetch('/api/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.message || 'Unable to fetch videos.');
    }

    const uniqueVideos = Array.isArray(data.videos) ? data.videos : [];

    summary.textContent = `Found ${data.totalUniqueVideos} unique videos (high impressions → low impressions).`;
    summary.classList.remove('hidden');

    if (!uniqueVideos.length) {
      setStatus('No videos found for this URL.');
      showDebug('✓ Request successful but 0 videos extracted.<br/>This might mean:<br/>1. Page has no ads<br/>2. GraphQL payload structure changed<br/>3. Playwright couldn\'t scroll properly');
      return;
    }

    setStatus('Done. You can preview or download videos below.');
    renderResults(uniqueVideos);
  } catch (error) {
    setStatus(error.message || 'Something went wrong.', true);
  } finally {
    submitBtn.disabled = false;
  }
});

// Log debug info in console for developer inspection
const originalFetch = window.fetch;
window.fetch = function(...args) {
  return originalFetch.apply(this, args).then(response => {
    if (args[0] === '/api/scrape') {
      response.clone().json().then(data => {
        if (data.debugLog) {
          console.log('=== SCRAPER DEBUG INFO ===');
          console.log('Payloads processed:', data.debugLog.payloadsProcessed);
          console.log('Total videos found in payloads:', data.debugLog.videosFound);
          console.log('Unique videos after dedup:', data.debugLog.uniqueVideos);
          if (data.debugLog.metadataStats) {
            console.log('Metadata extraction stats:', data.debugLog.metadataStats);
          }
          if (data.debugLog.warnings.length > 0) {
            console.warn('Warnings:', data.debugLog.warnings);
          }
        }
      });
    }
    return response;
  });
};
