/**
 * Site detection and router for multi-site car listing extraction
 */

const SUPPORTED_SITES = {
  cargurus: {
    name: 'CarGurus',
    urlPattern: /cargurus\.com/i,
    listingUrlPattern: /cargurus\.com.*viewDetailsFilterViewInventoryListing/i,
    extractor: 'cargurus'
  },
  autotrader: {
    name: 'AutoTrader',
    urlPattern: /autotrader\.com/i,
    listingUrlPattern: /autotrader\.com.*\/cars-for-sale\/vehicledetails/i,
    extractor: 'autotrader'
  },
  cars: {
    name: 'Cars.com',
    urlPattern: /cars\.com/i,
    listingUrlPattern: /cars\.com.*\/vehicledetail/i,
    extractor: 'cars'
  }
};

/**
 * Detect which site we're currently on
 * @returns {string|null} Site key (e.g., 'cargurus') or null if unsupported
 */
function detectCurrentSite() {
  const currentUrl = window.location.href;
  
  for (const [siteKey, siteConfig] of Object.entries(SUPPORTED_SITES)) {
    if (siteConfig.urlPattern.test(currentUrl)) {
      console.log(`🌐 Detected site: ${siteConfig.name} (${siteKey})`);
      return siteKey;
    }
  }
  
  console.log(`❌ Unsupported site: ${currentUrl}`);
  return null;
}

/**
 * Check if current URL is a listing page for the detected site
 * @param {string} siteKey - Site key from detectCurrentSite()
 * @returns {boolean} True if this is a listing page
 */
function isListingPage(siteKey) {
  if (!siteKey || !SUPPORTED_SITES[siteKey]) {
    return false;
  }
  
  const currentUrl = window.location.href;
  const isListing = SUPPORTED_SITES[siteKey].listingUrlPattern.test(currentUrl);
  
  console.log(`📄 Is listing page for ${siteKey}: ${isListing}`);
  return isListing;
}

/**
 * Get site configuration
 * @param {string} siteKey - Site key
 * @returns {object|null} Site configuration or null
 */
function getSiteConfig(siteKey) {
  return SUPPORTED_SITES[siteKey] || null;
}

/**
 * Get list of all supported sites
 * @returns {object} Object mapping site keys to configurations
 */
function getSupportedSites() {
  return SUPPORTED_SITES;
}