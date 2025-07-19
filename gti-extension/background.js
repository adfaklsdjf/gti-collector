chrome.action.onClicked.addListener((tab) => {
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: [
      "sites/site-detector.js",
      "sites/field-mapper.js", 
      "sites/cargurus-extractor.js",
      "sites/autotrader-extractor.js",
      "sites/cars-extractor.js",
      "content.js"
    ]
  });
});
