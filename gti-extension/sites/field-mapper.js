/**
 * Field mapping system for converting site-specific data to internal format
 */

// Define mapping from site-specific fields to internal fields
const SITE_FIELD_MAPPINGS = {
  cargurus: {
    // Direct mappings (site field -> internal field)
    'site': 'site',
    'url': 'url',
    'title': 'title',
    'price': 'price',
    'year': 'year',
    'mileage': 'mileage',
    'vin': 'vin',
    'location': 'location',
    'distance': 'distance',
    'drivetrain': 'drivetrain',
    'exterior_color': 'exterior_color',
    'interior_color': 'interior_color',
    'mpg': 'mpg',
    'engine': 'engine',
    'fuel_type': 'fuel_type',
    'transmission': 'transmission',
    'trim_level': 'trim_level',
    'car_title': 'car_title',
    'accidents': 'accidents',
    'previous_owners': 'previous_owners',
    'phone_number': 'phone_number'
  },
  edmunds: {
    // Edmunds-specific field mappings
    'site': 'site',
    'url': 'url',
    'Title': 'title',
    'Price': 'price',
    'Year': 'year',
    'Mileage': 'mileage',
    'VIN': 'vin',
    'Trim': 'trim_level',
    'Ext. Color': 'exterior_color',
    'Int. Color': 'interior_color',
    'Accidents': 'accidents',
    'Owners': 'previous_owners',
    'Stock #': 'stock_number',
    'Seller Name': 'seller_name',
    'Seller Location': 'location'
  },
  autotrader: {
    // TODO: Define AutoTrader field mappings
    'site': 'site',
    'url': 'url',
    'title': 'title'
    // Add more mappings as AutoTrader extraction is implemented
  },
  cars: {
    // TODO: Define Cars.com field mappings
    'site': 'site',
    'url': 'url',
    'title': 'title'
    // Add more mappings as Cars.com extraction is implemented
  }
};

// Define which internal fields are available from which sites
const SITE_CAPABILITIES = {
  cargurus: [
    'site', 'url', 'title', 'price', 'year', 'mileage', 'vin', 'location', 'distance',
    'drivetrain', 'exterior_color', 'interior_color', 'mpg', 'engine', 'fuel_type',
    'transmission', 'trim_level', 'car_title', 'accidents', 'previous_owners', 'phone_number'
  ],
  edmunds: [
    'site', 'url', 'title', 'price', 'year', 'mileage', 'vin', 'location',
    'exterior_color', 'interior_color', 'trim_level', 'accidents', 'previous_owners',
    'stock_number', 'seller_name'
  ],
  autotrader: [
    'site', 'url', 'title'
    // TODO: Add more capabilities as AutoTrader extraction is implemented
  ],
  cars: [
    'site', 'url', 'title'
    // TODO: Add more capabilities as Cars.com extraction is implemented
  ]
};

/**
 * Map site-specific extracted data to internal field format
 * @param {object} rawData - Raw extracted data from site extractor
 * @param {string} siteKey - Site key (e.g., 'cargurus')
 * @returns {object} Mapped data in internal format
 */
function mapFieldsToInternal(rawData, siteKey) {
  console.log(`🔄 Mapping ${siteKey} fields to internal format...`);

  const mapping = SITE_FIELD_MAPPINGS[siteKey];
  if (!mapping) {
    console.error(`❌ No field mapping found for site: ${siteKey}`);
    return {};
  }

  const mappedData = {};
  const capabilities = SITE_CAPABILITIES[siteKey] || [];

  // Process each field from raw data
  for (const [siteField, value] of Object.entries(rawData)) {
    if (value === null || value === undefined || value === '') {
      continue; // Skip empty values
    }

    let internalField = null;

    // First: Check for explicit mapping
    if (mapping[siteField]) {
      internalField = mapping[siteField];
      // console.log(`📋 Explicit mapping: ${siteField} -> ${internalField}`);
    }
    // Second: Look for direct name match
    else if (capabilities.includes(siteField)) {
      internalField = siteField;
      // console.log(`🎯 Direct match: ${siteField} -> ${internalField}`);
    }
    // Third: Log and drop unknown fields
    else {
      // console.log(`⚠️ Unknown field dropped: ${siteField} = "${value}"`);
      continue;
    }

    mappedData[internalField] = value;
    // console.log(`✅ Mapped: ${siteField} = "${value}" -> ${internalField}`);
  }

  console.log(`🔄 Field mapping complete for ${siteKey}:`, mappedData);
  return mappedData;
}

/**
 * Get list of fields supported by a site
 * @param {string} siteKey - Site key
 * @returns {array} Array of internal field names supported by the site
 */
function getSiteCapabilities(siteKey) {
  return SITE_CAPABILITIES[siteKey] || [];
}

/**
 * Check if a site supports a specific internal field
 * @param {string} siteKey - Site key
 * @param {string} internalField - Internal field name
 * @returns {boolean} True if site supports the field
 */
function siteSupportsField(siteKey, internalField) {
  const capabilities = SITE_CAPABILITIES[siteKey] || [];
  return capabilities.includes(internalField);
}
