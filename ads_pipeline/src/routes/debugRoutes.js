const express = require('express');
const fs = require('fs');
const path = require('path');

const router = express.Router();

router.get('/payloads', (_req, res) => {
  try {
    const dir = path.join(__dirname, '../../payload_debug');
    
    if (!fs.existsSync(dir)) {
      return res.json({
        ok: true,
        message: 'No payloads captured yet. Run a scrape first.',
        payloads: []
      });
    }

    const files = fs.readdirSync(dir).sort();
    const payloads = files.map(file => ({
      name: file,
      path: `/api/debug/payloads/${file}`
    }));

    res.json({
      ok: true,
      totalPayloads: payloads.length,
      payloads
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      message: error.message
    });
  }
});

router.get('/payloads/:filename', (req, res) => {
  try {
    const filename = req.params.filename;
    if (!filename.match(/^payload_\d+.*\.json$/)) {
      return res.status(400).json({ ok: false, message: 'Invalid filename' });
    }

    const filePath = path.join(__dirname, '../../payload_debug', filename);
    const content = fs.readFileSync(filePath, 'utf8');
    
    res.setHeader('Content-Type', 'application/json');
    res.send(content);
  } catch (error) {
    res.status(404).json({ ok: false, message: 'Payload not found' });
  }
});

router.delete('/payloads', (_req, res) => {
  try {
    const dir = path.join(__dirname, '../../payload_debug');
    
    if (fs.existsSync(dir)) {
      fs.rmSync(dir, { recursive: true });
    }

    res.json({ ok: true, message: 'Payloads cleared' });
  } catch (error) {
    res.status(500).json({
      ok: false,
      message: error.message
    });
  }
});

module.exports = router;
