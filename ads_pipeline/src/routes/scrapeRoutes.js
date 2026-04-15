const express = require('express');
const { scrapeFromUrl, streamVideoDownload } = require('../controllers/scrapeController');

const router = express.Router();

router.post('/scrape', scrapeFromUrl);
router.get('/download', streamVideoDownload);

module.exports = router;
