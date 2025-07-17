


// COLLECT TRIM LEVEL
const trimDiv = document.querySelector('div[data-cg-ft="trim"]');
let trimLevel = null;

if (trimDiv) {
  // Find the child div with the specific class
  const recordDiv = trimDiv.querySelector('div._record_1fvwn_1');

  if (recordDiv) {
    // Get all direct span children of recordDiv
    const spans = Array.from(recordDiv.querySelectorAll(':scope > span'));

    for (const span of spans) {
      // Check if any class in the classList starts with _value
      if (Array.from(span.classList).some(cls => cls.startsWith('_value'))) {
        trimLevel = span.textContent.trim();
        break; // Found the one we need
      }
    }
  }
}
if (trimLevel) {
  console.log("Trim Level:", trimLevel);
} else {
  console.log("Could not find the trim level element.");
}



// COLLECT TITLE, ACCIDENTS, PREVIOUS OWNERS
const categoriesData = [];
const categoriesDiv = document.querySelector('div._elements_1rs20_1');

if (categoriesDiv) {
  // Find all elements with the class _category_1jffh_1 within the parent
  const categoryElements = categoriesDiv.querySelectorAll(':scope > ._category_1jffh_1');

  categoryElements.forEach(categoryDiv => {
    const heading = categoryDiv.querySelector('h4');
    const paragraph = categoryDiv.querySelector('p');

    if (heading && paragraph) {
      categoriesData.push({
        title: heading.textContent.trim(),
        description: paragraph.textContent.trim()
      });
    }
  });
}

console.log(categoriesData);

// Example output structure
[
    {
        "title": "Clean title",
        "description": "No issues reported."
    },
    {
        "title": "2 accidents reported",
        "description": "No damage reported."
    },
    {
        "title": "4 previous owners",
        "description": "Vehicle has 4 previous owners."
    }
]

// I want this to be stored by the app in 3 fields:
// car_title: "Clean title - No issues reported."
// accidents: "2 accidents reported - No damage reported."
// previous_owners: "4 previous owners - Vehicle has 4 previous owners."



// COLLECT PHONE NUMBER
const callButton = document.querySelector('button[data-testid="ghost-call-btn"]');

let phoneNumber = null;

if (callButton) {
  // Iterate through child nodes to find the text node
  for (const node of callButton.childNodes) {
    // Check if the node is a text node and has non-empty content
    if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
      phoneNumber = node.textContent.trim();
      break; // Found the text node with the number, no need to continue
    }
  }
}


