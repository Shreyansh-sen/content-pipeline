const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: false // keep false for debugging
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // 🔥 Store unique videos
  const videoSet = new Set();

  // 🔥 Capture GraphQL responses (BEST SOURCE)
  page.on('response', async (response) => {
    try {
      const url = response.url();

      if (url.includes('graphql')) {
        const data = await response.json();

        const jsonStr = JSON.stringify(data);

        // extract all .mp4 URLs~
        const matches = jsonStr.match(/https?:\/\/[^\s"]+\.mp4[^\s"]*/g);

        if (matches) {
          matches.forEach(v => videoSet.add(v));
        }
      }

      // also capture direct media responses
      if (url.includes('.mp4')) {
        videoSet.add(url);
      }

    } catch (e) {
      // ignore parsing errors
    }
  });

  // 🌐 Open Ads Library
  await page.goto(
    'https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&search_type=page&view_all_page_id=160580977144612',
    { waitUntil: 'domcontentloaded' }
  );

  console.log("🌐 Page loaded...");

  // ⏳ wait initial load
  await page.waitForTimeout(5000);

  // 🔁 Scroll properly (IMPORTANT)
  await page.evaluate(async () => {
    for (let i = 0; i < 20; i++) {
      window.scrollBy(0, window.innerHeight);
      await new Promise(r => setTimeout(r, 2500));
    }
  });

  console.log("📜 Finished scrolling...");

  // ⏳ wait for final network calls
  await page.waitForTimeout(5000);

  // 🧹 Clean & filter valid videos
  const finalVideos = Array.from(videoSet)
    .filter(url => url.includes('.mp4'))
    .filter((url, index, self) => self.indexOf(url) === index);

  // 📊 Output results
  console.log("\n🎥 UNIQUE VIDEO URLS:\n");

  finalVideos.forEach((v, i) => {
    console.log(`${i + 1}. ${v}\n`);
  });

  console.log("📊 Total unique videos:", finalVideos.length);

  await browser.close();
})();
