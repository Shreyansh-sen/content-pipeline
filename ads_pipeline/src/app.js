const express = require('express');
const path = require('path');
const scrapeRoutes = require('./routes/scrapeRoutes');
const debugRoutes = require('./routes/debugRoutes');

function createApp() {
  const app = express();

  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true }));

  app.use('/api', scrapeRoutes);
  app.use('/api/debug', debugRoutes);
  app.use(express.static(path.join(__dirname, 'public')));

  app.get('/health', (_req, res) => {
    res.json({ ok: true, service: 'ads_pipeline_ui' });
  });

  return app;
}

module.exports = {
  createApp
};
