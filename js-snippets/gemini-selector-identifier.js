const valuesToFind = {
  "Title": "2017 Volkswagen Golf GTI 2.0T Autobahn 4-Door",
  "Year": "2017",
  "Trim": "",
  "Price": "16,495",
  "Mileage": "120,365",
  "Ext. Color": "Carbon Steel Gray Metallic",
  "Int. Color": "Titan Black w/Red Piping",
  "Stock #": "021667",
  "VIN": "3VW547AU2HM021667",
  "Accidents": "At least 1 accident or damage reported",
  "Owners": "2",
  "Seller Name": "Auto Sport Inc",
  "Seller Location": "3055 S Division Ave, Grand Rapids, MI 49548",
  "Seller contact": "(866) 735-6319"
};

const foundElements = {};
const notFoundValues = [];

for (const field in valuesToFind) {
  const value = valuesToFind[field];
  const elements = Array.from(document.querySelectorAll('*')).filter(el => el.textContent.includes(value));

  if (elements.length > 0) {
    // Prioritize elements with text nodes directly containing the value
    const directMatch = elements.find(el => Array.from(el.childNodes).some(node => node.nodeType === Node.TEXT_NODE && node.textContent.includes(value)));
    const element = directMatch || elements[0]; // Use direct match if found, otherwise the first found element
    foundElements[field] = {
      tagName: element.tagName,
      id: element.id,
      classes: Array.from(element.classList).join('.'),
      textContent: element.textContent.trim()
    };
  } else {
    notFoundValues.push(field);
  }
}

const data = {
  foundElements: foundElements,
  notFoundValues: notFoundValues
};
