const fs = require('fs');
const path = require('path');

let payloadIndex = 0;

function savePayloadForAnalysis(payload, label = '') {
  try {
    const dir = path.join(__dirname, '../../payload_debug');
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    payloadIndex += 1;
    const filename = path.join(dir, `payload_${payloadIndex}_${label}.json`);
    
    const truncated = {
      _meta: `Payload ${payloadIndex}`,
      _timestamp: new Date().toISOString(),
      _sample: JSON.stringify(payload).slice(0, 2000)
    };

    fs.writeFileSync(filename, JSON.stringify(truncated, null, 2));
    console.log(`📊 Payload saved: ${filename}`);
  } catch (error) {
    // silently fail
  }
}

module.exports = {
  savePayloadForAnalysis
};
