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
      console.log("CarGurus extractor returned:", rawCarDetails);
      break;
    case 'edmunds':
      rawCarDetails = extractEdmundsListing();
      console.log("Edmunds extractor returned:", rawCarDetails);
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
  console.log("📋 Remapped details:", carDetails);

  // Validate required fields (title and location are optional but preferred)
  const requiredFields = ['price', 'year', 'mileage', 'vin'];
  const missingFields = requiredFields.filter(field => !carDetails[field]);

  // Log optional fields status for debugging
  if (!carDetails.title) console.warn('⚠️ Title not extracted');
  if (!carDetails.location) console.warn('⚠️ Location not extracted');

  if (missingFields.length > 0) {
    console.warn(`❌ Missing required fields: ${missingFields.join(', ')}`);
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
      console.error('❌ Error sending data to backend:', error);
      showToast(`❌ Error: ${error.message}`, 'error');
    });
}

// Replace the simple alert with our main function
handleExtensionClick();
