const { createApp } = require('./app');

const PORT = Number(process.env.PORT || 3001);
const app = createApp();

app.listen(PORT, () => {
  console.log(`✅ Ads Pipeline UI running at http://localhost:${PORT}`);
});
