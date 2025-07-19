/**
 * CarGurus-specific data extraction logic
 */

/**
 * Extract car details from CarGurus listing page
 * @returns {object} Extracted car details
 */
function extractCarGurusListing() {
  console.log('🚗 Starting CarGurus extraction...');
  
  const carDetails = {
    site: 'cargurus',
    url: window.location.href
  };

  // Extract title
  console.log("Attempting to extract title...");
  const titleElement = document.querySelector('h1[data-cg-ft="vdp-listing-title"]') ||
                      document.querySelector('h1');
  if (titleElement) {
    carDetails.title = titleElement.textContent.trim();
    console.log(`Extracted title: "${carDetails.title}"`);
  } else {
    console.log("Could not find title element");
  }

  // Extract location and distance
  console.log("Attempting to extract location...");
  const locationElement = document.querySelector('hgroup._group_s8u01_1 p.oqywn.sCSIz') ||
                         document.querySelector('h1[data-cg-ft="vdp-listing-title"] + p') ||
                         Array.from(document.querySelectorAll('p')).find(p =>
                           p.textContent.match(/.*,\s*[A-Z]{2}\s*\(\d+\s*mi\s*away\)/i)
                         );
  if (locationElement) {
    const locationText = locationElement.textContent.trim();
    carDetails.location = locationText;
    console.log(`Extracted location: "${locationText}"`);

    // Try to parse distance from location (simple extraction for CarGurus)
    const distanceMatch = locationText.match(/\((\d+(?:,\d+)?)\s*mi\s*away\)/i);
    if (distanceMatch) {
      carDetails.distance = distanceMatch[1].replace(',', ''); // Remove commas for numeric format
      console.log(`Extracted distance: "${carDetails.distance}"`);
    }
  } else {
    console.log("Could not find location element");
  }

  // Extract price
  console.log("Attempting to extract price...");
  const priceElement = document.querySelector('.oqywn.FieH9');
  if (priceElement) {
    carDetails.price = priceElement.textContent.trim();
    console.log(`Extracted price: "${carDetails.price}"`);
  } else {
    console.log("No primary price element found, searching for potential prices...");
    const potentialPrices = Array.from(document.querySelectorAll('body *')).filter(el => {
      const text = el.textContent.trim();
      const rect = el.getBoundingClientRect();
      return text.includes('$') && /\d/.test(text) && rect.top < 500;
    });
    if (potentialPrices.length > 0) {
      const smallestPriceElement = potentialPrices.reduce((prev, curr) => {
        return (prev.getBoundingClientRect().height < curr.getBoundingClientRect().height) ? prev : curr;
      });
      carDetails.price = smallestPriceElement.textContent.trim();
      console.log(`Extracted price (fallback): "${carDetails.price}"`);
    }
  }

  // Extract mileage
  console.log("Attempting to extract mileage...");
  const h5Element = Array.from(document.querySelectorAll('h5')).find(el => el.textContent.includes('Mileage'));
  const mileageElement = h5Element ? h5Element.nextElementSibling : null;

  if (mileageElement) {
    console.log("mileageElement found:", mileageElement);
    if (mileageElement.tagName.toLowerCase() === 'p') {
      console.log("It's even a paragraph element!");
    }
    carDetails.mileage = mileageElement.textContent.trim();
    console.log(`Extracted mileage: "${carDetails.mileage}"`);
  } else {
    console.log("No mileageElement found, searching for potential mileage elements...");
    const potentialMileages = Array.from(document.querySelectorAll('body *')).filter(el => {
      const text = el.textContent.trim().toLowerCase();
      return (text.includes('mileage') || text.includes('mi')) && /\d/.test(text) && text.length < 50;
    });
    if (potentialMileages.length > 0) {
      const labeledMileage = potentialMileages.find(el =>
        el.textContent.trim().toLowerCase().startsWith('mileage:')
      );
      if (labeledMileage) {
        carDetails.mileage = labeledMileage.textContent.trim().replace(/mileage:\s*/i, '').trim();
      } else {
        carDetails.mileage = potentialMileages[0].textContent.trim();
      }
      console.log(`Extracted mileage (fallback): "${carDetails.mileage}"`);
    }
  }

  // Extract additional vehicle details using H5 + next element pattern
  const vehicleFields = [
    'Drivetrain',
    'Exterior Color',
    'Interior Color',
    'MPG',
    'Engine',
    'Fuel type',
    'Transmission'
  ];

  console.log("Attempting to extract additional vehicle fields...");
  vehicleFields.forEach(fieldName => {
    const h5Element = Array.from(document.querySelectorAll('h5')).find(el =>
      el.textContent.includes(fieldName)
    );
    const valueElement = h5Element ? h5Element.nextElementSibling : null;

    if (valueElement) {
      const fieldKey = fieldName.toLowerCase().replace(' ', '_');
      const fieldValue = valueElement.textContent.trim();
      carDetails[fieldKey] = fieldValue;
      console.log(`Extracted ${fieldName}: "${fieldValue}"`);
    } else {
      console.log(`Could not find ${fieldName} field`);
    }
  });

  // Extract trim level
  console.log("Attempting to extract trim level...");
  const trimDiv = document.querySelector('div[data-cg-ft="trim"]');
  if (trimDiv) {
    const recordDiv = trimDiv.querySelector('div._record_1fvwn_1');
    if (recordDiv) {
      const spans = Array.from(recordDiv.querySelectorAll(':scope > span'));
      for (const span of spans) {
        if (Array.from(span.classList).some(cls => cls.startsWith('_value'))) {
          carDetails.trim_level = span.textContent.trim();
          console.log(`Extracted trim level: "${carDetails.trim_level}"`);
          break;
        }
      }
    }
  }
  if (!carDetails.trim_level) {
    console.log("Could not find trim level element");
  }

  // Extract car title, accidents, and previous owners from categories
  console.log("Attempting to extract categories data (title, accidents, owners)...");
  const categoriesDiv = document.querySelector('div._elements_1rs20_1');
  if (categoriesDiv) {
    const categoryElements = categoriesDiv.querySelectorAll(':scope > ._category_1jffh_1');

    categoryElements.forEach(categoryDiv => {
      const heading = categoryDiv.querySelector('h4');
      const paragraph = categoryDiv.querySelector('p');

      if (heading && paragraph) {
        const title = heading.textContent.trim();
        const description = paragraph.textContent.trim();
        const combinedText = `${title} - ${description}`;

        // Determine which field this belongs to based on title content
        if (title.toLowerCase().includes('title')) {
          carDetails.car_title = combinedText;
          console.log(`Extracted car title: "${combinedText}"`);
        } else if (title.toLowerCase().includes('accident')) {
          carDetails.accidents = combinedText;
          console.log(`Extracted accidents: "${combinedText}"`);
        } else if (title.toLowerCase().includes('owner')) {
          carDetails.previous_owners = combinedText;
          console.log(`Extracted previous owners: "${combinedText}"`);
        }
      }
    });
  } else {
    console.log("Could not find categories div for title/accidents/owners");
  }

  // Extract phone number
  console.log("Attempting to extract phone number...");
  const callButton = document.querySelector('button[data-testid="ghost-call-btn"]');
  if (callButton) {
    for (const node of callButton.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
        carDetails.phone_number = node.textContent.trim();
        console.log(`Extracted phone number: "${carDetails.phone_number}"`);
        break;
      }
    }
  }
  if (!carDetails.phone_number) {
    console.log("Could not find phone number element");
  }

  // Extract year and VIN from records
  console.log("Attempting to extract year and VIN...");
  const records = document.querySelectorAll('._record_1fvwn_1');
  records.forEach(record => {
    const text = record.textContent.trim();
    if (text.startsWith('Year:')) {
      carDetails.year = text.replace('Year:', '').trim();
      console.log(`Extracted year: "${carDetails.year}"`);
    } else if (text.startsWith('VIN:')) {
      carDetails.vin = text.replace('VIN:', '').trim();
      console.log(`Extracted VIN: "${carDetails.vin}"`);
    }
  });

  // Fallback year extraction
  if (!carDetails.year) {
    console.log("Attempting fallback year extraction...");
    const yearElement = Array.from(document.querySelectorAll('body *')).find(el =>
      el.textContent.trim().match(/Year:\s*\d{4}/)
    );
    if (yearElement) {
      const yearMatch = yearElement.textContent.trim().match(/Year:\s*(\d{4})/);
      if (yearMatch) {
        carDetails.year = yearMatch[1];
        console.log(`Extracted year (fallback): "${carDetails.year}"`);
      }
    }
  }

  // Fallback VIN extraction
  if (!carDetails.vin) {
    console.log("Attempting fallback VIN extraction...");
    const vinElement = Array.from(document.querySelectorAll('body *')).find(el =>
      el.textContent.trim().match(/VIN:\s*[A-HJ-NPR-Z0-9]{17}/i)
    );
    if (vinElement) {
      const vinMatch = vinElement.textContent.trim().match(/VIN:\s*([A-HJ-NPR-Z0-9]{17})/i);
      if (vinMatch) {
        carDetails.vin = vinMatch[1];
        console.log(`Extracted VIN (fallback): "${carDetails.vin}"`);
      }
    }
  }

  console.log('✅ CarGurus extraction complete:', carDetails);
  return carDetails;
}