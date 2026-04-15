function extractVideoUrlsFromObject(value) {
  const urls = new Set();

  try {
    const jsonStr = JSON.stringify(value);
    const matches = jsonStr.match(/https?:\/\/[^\s"'\\]+\.mp4[^\s"'\\]*/gi);

    if (matches) {
      matches.forEach((url) => urls.add(url));
    }
  } catch (error) {
    // ignore non-serializable structures
  }

  return [...urls];
}

module.exports = {
  extractVideoUrlsFromObject
};
