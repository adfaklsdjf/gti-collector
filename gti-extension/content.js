console.log("🚗 GTI Extension content script injected");

// Create toast notification
function showToast(message, type = 'info', duration = 3000) {
  // Remove any existing toast
  const existingToast = document.getElementById('gti-extension-toast');
  if (existingToast) {
    existingToast.remove();
  }

  // Create toast element
  const toast = document.createElement('div');
  toast.id = 'gti-extension-toast';
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.3s ease;
    max-width: 300px;
    word-wrap: break-word;
  `;

  // Set color based on type
  const colors = {
    success: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
    info: '#3B82F6',
    duplicate: '#8B5CF6'
  };
  toast.style.backgroundColor = colors[type] || colors.info;

  // Set message
  toast.textContent = message;

  // Add to page
  document.body.appendChild(toast);

  // Auto-remove after duration
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }
  }, duration);
}

// Check if this is a CarGurus listing page
function isCarGurusListingPage() {
  return window.location.hostname.includes('cargurus.com') &&
         (window.location.pathname.includes('/vdp.action') ||
          window.location.pathname.includes('viewDetailsFilterViewInventoryListing.action'));
}

// Extract car details from CarGurus page
function extractCarGurusDetails() {
  const carDetails = {
    url: window.location.href
  };

  // Extract title using robust selectors
  const titleElement = document.querySelector('h1[data-cg-ft="vdp-listing-title"]') ||
                      document.querySelector('._listingHeading_s8u01_6') ||
                      document.querySelector('h1.oqywn._0ZnFt') ||
                      document.querySelector('h1');
  if (titleElement) {
    carDetails.title = titleElement.textContent.trim();
  }

  // Extract location from the paragraph following the title
  const locationElement = document.querySelector('hgroup._group_s8u01_1 p.oqywn.sCSIz') ||
                         document.querySelector('h1[data-cg-ft="vdp-listing-title"] + p') ||
                         Array.from(document.querySelectorAll('p')).find(p =>
                           p.textContent.match(/.*,\s*[A-Z]{2}\s*\(\d+\s*mi\s*away\)/i)
                         );
  if (locationElement) {
    const locationText = locationElement.textContent.trim();
    carDetails.location = locationText;

    // Try to parse distance more precisely from location
    const distanceMatch = locationText.match(/\((\d+)\s*mi\s*away\)/i);
    if (distanceMatch) {
      carDetails.distance = `${distanceMatch[1]} mi away`;
    }
  }

  // Extract price
  const priceElement = document.querySelector('.oqywn.FieH9');
  if (priceElement) {
    carDetails.price = priceElement.textContent.trim();
  } else {
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
    }
  }

  // Extract mileage
  // const mileageElement = document.querySelector('.oqywn.sCSIz._value_1fvwn_13');
  const h5Element = Array.from(document.querySelectorAll('h5')).find(el => el.textContent.includes('Mileage'));
  const mileageElement = h5Element ? h5Element.nextElementSibling : null;

  if (mileageElement) {
    console.log("mileageElement found:", mileageElement);
    if (mileageElement.tagName.toLowerCase() === 'p') {
      console.log("It's even a paragraph element!");
    }
    carDetails.mileage = mileageElement.textContent.trim();
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
  const records = document.querySelectorAll('._record_1fvwn_1');
  records.forEach(record => {
    const text = record.textContent.trim();
    if (text.startsWith('Year:')) {
      carDetails.year = text.replace('Year:', '').trim();
    } else if (text.startsWith('VIN:')) {
      carDetails.vin = text.replace('VIN:', '').trim();
    }
  });

  // Fallback year extraction
  if (!carDetails.year) {
    const yearElement = Array.from(document.querySelectorAll('body *')).find(el =>
      el.textContent.trim().match(/Year:\s*\d{4}/)
    );
    if (yearElement) {
      carDetails.year = yearElement.textContent.trim().replace('Year:', '').trim();
    }
  }

  // Fallback VIN extraction
  if (!carDetails.vin) {
    const vinElement = Array.from(document.querySelectorAll('body *')).find(el =>
      el.textContent.trim().match(/VIN:\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}/i)
    );
    if (vinElement) {
      carDetails.vin = vinElement.textContent.trim().replace('VIN:', '').trim();
    }
  }

  // Add fallback distance if not extracted from location
  if (!carDetails.distance) {
    carDetails.distance = "Unknown";
  }

  return carDetails;
}

// Send data to Flask backend
async function sendToBackend(carDetails) {
  console.log('🚗 Complete car details being sent to backend:', carDetails);
  try {
    const response = await fetch('http://127.0.0.1:5000/listings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(carDetails)
    });

    const result = await response.json();
    console.log('📤 Backend response:', result);
    return result;
  } catch (error) {
    console.error('❌ Error sending to backend:', error);
    throw error;
  }
}

// Main function when extension is activated
function handleExtensionClick() {
  // Detect current site and check if it's a supported listing page
  const currentSite = detectCurrentSite();
  if (!currentSite) {
    showToast('❌ This site is not yet supported', 'error');
    return;
  }

  if (!isListingPage(currentSite)) {
    showToast(`❌ Please navigate to a ${getSiteConfig(currentSite).name} listing page`, 'error');
    return;
  }

  console.log(`🔍 Extracting car details from ${getSiteConfig(currentSite).name}...`);
  showToast("🔍 Extracting listing data...", 'info', 2000);

  // Use site-specific extractor
  let rawCarDetails = {};
  switch (currentSite) {
    case 'cargurus':
      rawCarDetails = extractCarGurusListing();
      break;
    case 'autotrader':
      rawCarDetails = extractAutoTraderListing();
      break;
    case 'cars':
      rawCarDetails = extractCarsListing();
      break;
    default:
      showToast(`❌ Extractor not implemented for ${currentSite}`, 'error');
      return;
  }

  // Map site-specific fields to internal format
  const carDetails = mapFieldsToInternal(rawCarDetails, currentSite);
  console.log("📋 Extracted details:", carDetails);

  // Validate required fields (title and location are optional but preferred)
  const requiredFields = ['price', 'year', 'mileage', 'vin'];
  const missingFields = requiredFields.filter(field => !carDetails[field]);

  // Log optional fields status for debugging
  if (!carDetails.title) console.warn('⚠️ Title not extracted');
  if (!carDetails.location) console.warn('⚠️ Location not extracted');

  if (missingFields.length > 0) {
    showToast(`❌ Missing required fields: ${missingFields.join(', ')}`, 'error');
    return;
  }

  // Send to backend
  sendToBackend(carDetails)
    .then(result => {
      if (result.updated === true) {
        // Listing was updated
        showToast(`🔄 Listing updated successfully!`, 'success');
      } else if (result.updated === false && result.message.includes('No changes')) {
        // No changes detected
        showToast(`ℹ️ No changes detected`, 'info');
      } else {
        // New listing created
        showToast(`✅ NEW listing saved successfully!`, 'success');
      }
    })
    .catch(error => {
      showToast(`❌ Error: ${error.message}`, 'error');
    });
}

// Replace the simple alert with our main function
handleExtensionClick();
