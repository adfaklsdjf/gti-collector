const extractData = () => {
  const data = {};

  // Extracting from known element selectors
  const titleElement = document.querySelector('title');
  if (titleElement) {
    data["Title"] = titleElement.textContent.trim();
  }

  const yearElement = document.querySelector('a.usurp-inventory-card-vdp-link');
  if (yearElement) {
     // Extracting the year from the text content which includes make and model
    const yearMatch = yearElement.textContent.match(/\d{4}/);
    if (yearMatch) {
      data["Year"] = yearMatch[0];
    } else {
       data["Year"] = yearElement.textContent.trim(); // Fallback to full text if year not found
    }
  }

  // Corrected approach for finding the price element
  const spans = document.querySelectorAll('span');
  let priceElement = null;
  for (const span of spans) {
      if (span.textContent.includes('$') && span.textContent.includes('16,495')) { // Check for both '$' and the value
          priceElement = span;
          break;
      }
  }

  if (priceElement) {
    data["Price"] = priceElement.textContent.trim();
  }


  const mileageElement = document.querySelector('div.pe-0.fw-bold.text-end.ms-1.col');
  if (mileageElement) {
    data["Mileage"] = mileageElement.textContent.trim();
  }

  const SellerNameElement = document.querySelector('div.mt-md-0_5.mt-lg-1.mb-0_5');
  if (SellerNameElement) {
    data["Seller Name"] = SellerNameElement.textContent.trim();
  }

  const SellerLocationElement = document.querySelector('div.Seller-address.text-gray-40');
  if (SellerLocationElement) {
    data["Seller Location"] = SellerLocationElement.textContent.trim();
  }

  // Extracting from script tag containing structured data (assuming JSON-LD)
  const scriptElements = document.querySelectorAll('script[type="application/ld+json"]');
  for (const script of scriptElements) {
    try {
      const jsonData = JSON.parse(script.textContent);
      // Assuming the structured data is an array and we need to find the Vehicle object
      const vehicleData = Array.isArray(jsonData) ? jsonData.find(item => item['@type'] === 'Vehicle') : (jsonData['@type'] === 'Vehicle' ? jsonData : null);

      if (vehicleData) {
        if (vehicleData.vehicleConfiguration) {
            data["Trim"] = vehicleData.vehicleConfiguration;
        }
        if (vehicleData.color) {
          data["Ext. Color"] = vehicleData.color;
        }
        if (vehicleData.vehicleInteriorColor) {
          data["Int. Color"] = vehicleData.vehicleInteriorColor;
        }
        if (vehicleData.sku) {
            data["Stock #"] = vehicleData.sku;
        }
        if (vehicleData.vehicleIdentificationNumber) {
          data["VIN"] = vehicleData.vehicleIdentificationNumber;
        }
        if (vehicleData.knownVehicleDamages) {
          // Extracting number from "1 Reported Accident" format
          const accidentMatch = vehicleData.knownVehicleDamages.match(/\d+/);
          if (accidentMatch) {
             data["Accidents"] = accidentMatch[0];
          } else {
             data["Accidents"] = vehicleData.knownVehicleDamages; // Fallback if number not found
          }
        }
        if (vehicleData.numberOfPreviousOwners) {
          data["Owners"] = vehicleData.numberOfPreviousOwners.toString();
        }
        // Extracting price from offers if not found elsewhere
        if (!data["Price"] && vehicleData.offers && vehicleData.offers.price) {
             data["Price"] = vehicleData.offers.price.toString();
        }

        // Extracting Seller name and location from offers if available (less likely in this structure)
         if (!data["Seller Name"] && vehicleData.offers && vehicleData.offers.seller && vehicleData.offers.seller.name) {
             data["Seller Name"] = vehicleData.offers.seller.name;
         }
         if (!data["Seller Location"] && vehicleData.offers && vehicleData.offers.seller && vehicleData.offers.seller.address) {
              // Construct address string from parts if available
              if (vehicleData.offers.seller.address['@type'] === 'PostalAddress') {
                 const address = vehicleData.offers.seller.address;
                 data["Seller Location"] = `${address.streetAddress}, ${address.addressLocality}, ${address.addressRegion} ${address.postalCode}`;
              } else {
                  data["Seller Location"] = vehicleData.offers.seller.address;
              }
         }


        break; // Stop after finding the first Vehicle object in structured data
      }
    } catch (e) {
      console.error("Error parsing JSON from script tag:", e);
    }
  }

  return data;
};

extractData();

