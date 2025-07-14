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
  const mileageElement = document.querySelector('.oqywn.sCSIz._value_1fvwn_13'); 
  if (mileageElement) {
    carDetails.mileage = mileageElement.textContent.trim();
  } else {
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
  if (!isCarGurusListingPage()) {
    showToast("⚠️ This extension only works on CarGurus vehicle listing pages", 'warning');
    return;
  }
  
  console.log("🔍 Extracting car details from CarGurus...");
  showToast("🔍 Extracting listing data...", 'info', 2000);
  
  const carDetails = extractCarGurusDetails();
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
        showToast(`✅ New listing saved successfully!`, 'success');
      }
    })
    .catch(error => {
      showToast(`❌ Error: ${error.message}`, 'error');
    });
}

// Replace the simple alert with our main function
handleExtensionClick();
