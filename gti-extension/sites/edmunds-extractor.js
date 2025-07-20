/**
 * Edmunds.com listing extractor
 * Extracts vehicle listing data from Edmunds vehicle detail pages
 */

/**
 * Extract car listing data from Edmunds page
 * @returns {object} Extracted car details
 */
function extractEdmundsListing() {
  console.log('🔍 Extracting car details from Edmunds...');

  const data = {};

  // Add site identifier and URL
  data.site = 'edmunds';
  data.url = window.location.href;

  // Extracting from known element selectors
  const titleElement = document.querySelector('title');
  if (titleElement) {
    data.Title = titleElement.textContent.trim();
  }

  // extract year from title
  const yearMatch = data.Title.match(/(20[12][0-9])/i);
  if (yearMatch) {
      data.year = yearMatch[1]; // Remove commas for numeric format
      console.log(`Extracted year: "${data.year}"`);
  } else {
    console.log("Could not find location element");
  }

  // Find price element by looking for spans containing price
  const spans = document.querySelectorAll('span');
  let priceElement = null;
  for (const span of spans) {
    const text = span.textContent;
    if (text.includes('$') && /\$\d{2,}/.test(text)) {
      console.log(`Probably price element: "${text}"`);
      // Extract just the numeric value without $ for Edmunds format
      const priceMatch = text.match(/\$(\d[\d,]*)/);
      if (priceMatch) {
        data.Price = priceMatch[1].replace(/,/g, '');
        break;
      }
    }
  }

  const mileageElement = document.querySelector('div.pe-0.fw-bold.text-end.ms-1.col');
  if (mileageElement) {
    data.Mileage = mileageElement.textContent.trim();
  }

  const dealerInfoElement = document.querySelector('div[data-test="dealer-info"]');
  if (dealerInfoElement) {
    const sellerNameElement = dealerInfoElement.querySelector('h3.dealer-name');
    if (sellerNameElement) {
      data['Seller Name'] = sellerNameElement.textContent.trim();
    }

    const sellerLocationElement = dealerInfoElement.querySelector('div.dealer-address');
    if (sellerLocationElement) {
      data['Seller Location'] = sellerLocationElement.textContent.trim();
    }
  }

  // Extracting from script tag containing structured data (JSON-LD)
  const scriptElements = document.querySelectorAll('script[type="application/ld+json"]');
  for (const script of scriptElements) {
    try {
      const jsonData = JSON.parse(script.textContent);
      // Find the Vehicle object in structured data
      const vehicleData = Array.isArray(jsonData)
        ? jsonData.find(item => item['@type'] === 'Vehicle')
        : (jsonData['@type'] === 'Vehicle' ? jsonData : null);

      if (vehicleData) {
        if (vehicleData.vehicleConfiguration) {
          data.Trim = vehicleData.vehicleConfiguration;
        }
        if (vehicleData.color) {
          data['Ext. Color'] = vehicleData.color;
        }
        if (vehicleData.vehicleInteriorColor) {
          data['Int. Color'] = vehicleData.vehicleInteriorColor;
        }
        if (vehicleData.sku) {
          console.log(`Extracted stock number: "${vehicleData.sku}"`);
          data['Stock Number'] = vehicleData.sku;
        }
        if (vehicleData.vehicleIdentificationNumber) {
          data.VIN = vehicleData.vehicleIdentificationNumber;
        }
        if (vehicleData.knownVehicleDamages) {
          // Handle different accident formats
          if (vehicleData.knownVehicleDamages.toLowerCase().includes('no reported')) {
            data.Accidents = 'No Reported Accidents';
          } else {
            // Try to extract number from "1 Reported Accident" format
            const accidentMatch = vehicleData.knownVehicleDamages.match(/\d+/);
            if (accidentMatch) {
              data.Accidents = accidentMatch[0];
            } else {
              data.Accidents = vehicleData.knownVehicleDamages;
            }
          }
        }
        if (vehicleData.numberOfPreviousOwners) {
          data.Owners = vehicleData.numberOfPreviousOwners.toString();
        }

        // Extract price from offers if not found elsewhere
        if (!data.Price && vehicleData.offers && vehicleData.offers.price) {
          // Convert to string and remove commas for consistency
          data.Price = vehicleData.offers.price.toString().replace(/,/g, '');
        }

        // Extract seller info from offers if available
        if (!data['Seller Name'] && vehicleData.offers && vehicleData.offers.seller && vehicleData.offers.seller.name) {
          data['Seller Name'] = vehicleData.offers.seller.name;
        }
        if (!data['Seller Location'] && vehicleData.offers && vehicleData.offers.seller && vehicleData.offers.seller.address) {
          // Construct address string from parts if available
          if (vehicleData.offers.seller.address['@type'] === 'PostalAddress') {
            const address = vehicleData.offers.seller.address;
            data['Seller Location'] = `${address.streetAddress}, ${address.addressLocality}, ${address.addressRegion} ${address.postalCode}`;
          } else {
            data['Seller Location'] = vehicleData.offers.seller.address;
          }
        }

        break; // Stop after finding the first Vehicle object in structured data
      }
    } catch (e) {
      console.error("Error parsing JSON from script tag:", e);
    }
  }

  console.log('📋 Extracted Edmunds data:', data);
  return data;
}

// Export for use in content script
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { extractEdmundsListing };
}
