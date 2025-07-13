console.log("🚗 GTI Extension content script injected");

// Check if this is a CarGurus listing page
function isCarGurusListingPage() {
  return window.location.hostname.includes('cargurus.com') && 
         window.location.pathname.includes('/vdp.action');
}

// Extract car details from CarGurus page
function extractCarGurusDetails() {
  const carDetails = {
    url: window.location.href
  };
  
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
  
  // Add placeholder distance for now
  carDetails.distance = "Unknown";
  
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
    alert("⚠️ This extension only works on CarGurus vehicle detail pages (VDP)");
    return;
  }
  
  console.log("🔍 Extracting car details from CarGurus...");
  const carDetails = extractCarGurusDetails();
  console.log("📋 Extracted details:", carDetails);
  
  // Validate required fields
  const requiredFields = ['price', 'year', 'mileage', 'vin'];
  const missingFields = requiredFields.filter(field => !carDetails[field]);
  
  if (missingFields.length > 0) {
    alert(`❌ Missing required fields: ${missingFields.join(', ')}`);
    return;
  }
  
  // Send to backend
  sendToBackend(carDetails)
    .then(result => {
      if (result.message.includes('already exists')) {
        alert(`♻️ Duplicate: ${result.message}`);
      } else {
        alert(`✅ Success: ${result.message}`);
      }
    })
    .catch(error => {
      alert(`❌ Error: ${error.message}`);
    });
}

// Replace the simple alert with our main function
handleExtensionClick();
