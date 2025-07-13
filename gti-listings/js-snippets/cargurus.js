(function() {
  'use strict';

  function extractCarDetails() {
    const carDetails = {};
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
    const mileageElement = document.querySelector('.oqywn.sCSIz._value_1fvwn_13'); 
    if (mileageElement) {
      carDetails.mileage = mileageElement.textContent.trim();
    } else {
        const potentialMileages = Array.from(document.querySelectorAll('body *')).filter(el => {
            const text = el.textContent.trim().toLowerCase();
            return (text.includes('mileage') || text.includes('mi')) && /\d/.test(text) && text.length < 50; 
        });
         if (potentialMileages.length > 0) {
            const labeledMileage = potentialMileages.find(el => el.textContent.trim().toLowerCase().startsWith('mileage:'));
            if (labeledMileage) {
                 carDetails.mileage = labeledMileage.textContent.trim().replace('Mileage:', '').trim();
            } else {
               carDetails.mileage = potentialMileages[0].textContent.trim(); 
            }
        }
    }
    const records = document.querySelectorAll('._record_1fvwn_1');
    records.forEach(record => {
      const text = record.textContent.trim();
      if (text.startsWith('Year:')) {
        carDetails.year = text.replace('Year:', '').trim();
      } else if (text.startsWith('VIN:')) {
        carDetails.vin = text.replace('VIN:', '').trim();
      }
    });
    if (!carDetails.year) {
        const yearElement = Array.from(document.querySelectorAll('body *')).find(el => el.textContent.trim().match(/Year:\s*\d{4}/));
        if (yearElement) {
            carDetails.year = yearElement.textContent.trim().replace('Year:', '').trim();
        }
    }
     if (!carDetails.vin) {
        const vinElement = Array.from(document.querySelectorAll('body *')).find(el => el.textContent.trim().match(/VIN:\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}/i));
        if (vinElement) {
            carDetails.vin = vinElement.textContent.trim().replace('VIN:', '').trim();
        }
    }


    return carDetails;
  }

  const details = extractCarDetails();
  console.log("Extracted Car Details:", details);

})();
