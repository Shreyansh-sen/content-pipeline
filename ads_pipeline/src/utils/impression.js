function parseMagnitude(rawNumber, suffix = '') {
  if (!rawNumber) return null;

  const normalized = String(rawNumber).replace(/,/g, '.').trim();
  const numeric = Number(normalized);
  if (Number.isNaN(numeric)) return null;

  const unit = suffix.toUpperCase();
  const multiplierMap = {
    K: 1_000,
    M: 1_000_000,
    B: 1_000_000_000
  };

  return Math.round(numeric * (multiplierMap[unit] || 1));
}

function extractImpressionRange(text) {
  if (typeof text !== 'string') return null;

  const source = text.replace(/\s+/g, ' ').trim();
  if (!/impression/i.test(source)) return null;

  const matches = [...source.matchAll(/(\d+(?:[.,]\d+)?)\s*([KMB]?)/gi)]
    .map(([, value, suffix]) => parseMagnitude(value, suffix))
    .filter((value) => Number.isFinite(value));

  if (!matches.length) return null;

  let min = Math.min(...matches);
  let max = Math.max(...matches);

  if (/less than/i.test(source) && matches.length === 1) {
    min = 0;
    max = matches[0];
  }

  return {
    text: source,
    min,
    max,
    score: max
  };
}

module.exports = {
  extractImpressionRange
};
