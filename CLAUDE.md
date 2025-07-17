# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GTI Listings Collector** - A local Flask app with browser extension for collecting and managing used Volkswagen GTI listings from car websites. Emphasizes incremental development, comprehensive testing, and clean architecture.

## Current Architecture

### Backend (Python/Flask) - Modular Structure
- **Flask app** (`app.py`) - Main application initialization (33 lines)
- **Configuration** (`config.py`) - Logging setup and application configuration
- **Routes** (`routes/`) - Modular route handlers by functionality:
  - `listings.py` - Main listing page and POST endpoint for new listings
  - `individual.py` - Individual listing detail page with edit foundation
  - `health.py` - Health check endpoint
- **Store class** (`store.py`) - File-based storage with VIN deduplication and upsert logic
- **Listing utilities** (`listing_utils.py`) - Data comparison, merging, and change detection
- **Storage format**: Individual JSON files per listing + VIN index for fast lookups

### Frontend (Browser Extension)
- **Browser extension** (`gti-extension/`) - Chrome/Brave extension for CarGurus.com
- **Content script** (`content.js`) - Extracts listing data, sends to local Flask API
- **Smart toast notifications** - Success/update/no-change feedback to user
- **Robust selectors** - Multiple fallback strategies for brittle generated class names

### Web Interface - Template System
- **Templates** (`templates/`) - Jinja2 templates with inheritance:
  - `base.html` - Common layout and styling foundation
  - `index.html` - Main listings page with responsive card grid
  - `listing_detail.html` - Individual listing detail page
- **Listings display** - Responsive card-based layout at `http://127.0.0.1:5000/`
- **Individual listing pages** - Detailed view at `/listing/<id>` ready for editable fields
- **Price sorting** - Listings sorted low to high for easy comparison
- **Navigation** - Breadcrumb navigation and clickable listing titles

## Key Features Working

### Data Collection
- **VIN-based deduplication** with intelligent upsert behavior
- **Title and location extraction** with multiple selector fallbacks
- **Required fields**: url, price, year, mileage, vin
- **Optional fields**: title, location, distance (preserved when available)
- **Distance extraction**: Automatically extracted from location text patterns like "City, State (123 mi away)"
- **Change detection**: Updates existing listings with new/changed data only

### User Experience
- **Smart notifications**: Different messages for new/updated/no-change
- **URL validation**: Only works on CarGurus listing pages
- **Error handling**: Clear feedback for missing fields or connection issues
- **Auto-reload**: Flask restarts automatically on code changes

### Data Integrity
- **Comprehensive logging** to `app.log` with change summaries
- **Defensive directory creation** - handles missing data folders gracefully
- **Robust error handling** throughout stack

## Development Workflow

### Essential Commands
```bash
# Start Flask app (auto-reloads on changes)
source venv/bin/activate && python app.py

# Run all tests (ALWAYS activate venv first)
source venv/bin/activate && python -m pytest -v

# Run specific test file (ALWAYS activate venv first)
source venv/bin/activate && python -m pytest test_store.py -v

# Install new dependencies
source venv/bin/activate && pip install package_name
```

### Browser Extension Development
1. Load unpacked extension in Chrome/Brave (`chrome://extensions/`)
2. Enable "Developer mode" toggle
3. Point to `gti-extension/` directory
4. **After code changes**: Click reload button on extension card
5. Test on CarGurus listing pages (URLs with `viewDetailsFilterViewInventoryListing.action`)

### Git Workflow
- **Always create git commit at end of every completed task**
- Use descriptive commit messages with bullet points
- Include "🤖 Generated with Claude Code" footer
- Add new files/patterns to `.gitignore` as needed
- Current ignored: `*.log`, `__pycache__/`, `data/`, `.pytest_cache/`, `*.pyc`, `app_old.py`

## Testing Philosophy

**Goal**: Minimize debug loops by catching errors autonomously through comprehensive testing.

### Current Coverage (37 tests)
- **Unit tests**: Store class (10 tests) - VIN deduplication, upserts, file operations, individual retrieval
- **Integration tests**: Flask endpoints (16 tests) - API functionality, individual pages, error handling, CORS
- **Utility tests**: listing_utils module (11 tests) - data comparison, merging, formatting

### Testing Approach
- **Isolated test environments** - each test uses dedicated Flask app with temporary store
- **Comprehensive fixtures** for reusable test data
- **Error scenario coverage** - missing fields, invalid data, file system issues
- **pytest configuration** with verbose output and clean tracebacks
- **Add tests when adding features** to maintain safety net
- **Modular test structure** - mirrors application structure for easy maintenance

## Development Guidelines

### Incremental Approach
- **Highly incremental development** - small testable steps
- **Avoid doing too much at once** to prevent bugfixing spirals
- **No file should exceed ~100 lines** to maintain simplicity
- **Verify each step before proceeding** to next feature
- **Break complex features into multiple commits**

### Code Organization
- **Modular design** - separate concerns into focused modules (~50-100 lines each)
- **Template inheritance** - base templates with specialized extensions
- **Route organization** - logical grouping by functionality
- **Light refactoring** when adding features, not wholesale rewrites
- **Defensive programming** - handle missing directories, network failures, etc.
- **Comprehensive logging** for debugging and monitoring

### Field Management
- **Required vs Optional distinction** is crucial for future expansion
- **Optional fields preserved** when new extraction provides None/empty values
- **Change detection** only triggers on meaningful value differences
- **Extensible field system** ready for additional data types

## Recent Major Changes

### App.py Refactoring (July 2025)
- **Broke down 600+ line monolithic app.py** into focused modules
- **Introduced template system** with proper Jinja2 inheritance
- **Created individual listing pages** at `/listing/<id>` as foundation for editable fields
- **Improved test isolation** with dedicated test Flask app
- **Enhanced maintainability** with clear separation of concerns

### Individual Listing Pages
- **Detailed car view** with enhanced styling and layout
- **Navigation breadcrumbs** for better user experience
- **Prominent VIN display** and metadata sections
- **Action buttons** for external links and navigation
- **Future enhancement area** clearly marked for user-editable fields

## Future Expansion Areas

### User-Editable Fields (Next Priority)
- **Personal notes** - text area for user comments and observations
- **Favorites system** - bookmark interesting listings
- **Custom tags** - user-defined categories and labels
- **Price alerts** - notifications when price changes
- **Comparison tools** - side-by-side listing comparison

### Additional Fields
- **Simple fields first** (dealer info, listing age, trim levels)
- **Complex fields later** (images, detailed specs, package detection)
- **Calculated fields** (price per mile, depreciation estimates)

### Multiple Sites Support
- **Site-specific extraction scripts** with shared core logic
- **Field variation handling** (some sites have different available data)
- **Fallback strategies** for missing data across sites

### Extension Functionality
- **Additional car sites** beyond CarGurus
- **Improved extraction reliability** with better selectors
- **Batch operations** and automation features
- **Site-specific customizations**

### Storage Layer Evolution
- **Loose coupling** to enable backend changes later
- **Potential migration** to SQLite, PostgreSQL, or cloud storage
- **Maintain VIN-based deduplication** regardless of backend

### Web Interface Improvements
- **Filtering and sorting** options beyond price
- **Export functionality** (CSV, spreadsheets)
- **Image previews** when available from listings
- **Advanced search and comparison** tools
- **User management** for multi-user scenarios
- **Dashboard analytics** - market trends, price analysis

## Current Data Schema

### Listing Object
```json
{
  "id": "uuid",
  "data": {
    "url": "string (required)",
    "price": "string (required)", 
    "year": "string (required)",
    "mileage": "string (required)",
    "distance": "string (optional, auto-extracted from location)",
    "vin": "string (required, unique)",
    "title": "string (optional)",
    "location": "string (optional)"
  }
}
```

### API Responses
- **201**: New listing created
- **200**: Listing updated or no changes detected
- **400**: Validation errors (missing fields, invalid JSON)
- **500**: Server errors

## Important Notes

### CarGurus Extraction
- **Primary selectors**: `data-cg-ft="vdp-listing-title"`, `hgroup._group_s8u01_1`
- **Fallback strategies**: Multiple class name attempts, regex patterns
- **Brittle class names**: `oqywn`, `sCSIz` may change - always provide fallbacks
- **Distance parsing**: Extract from location text like "Cleveland, OH (15 mi away)"

### Testing Requirements
- **Test isolation**: Each test uses temporary directories
- **Comprehensive scenarios**: Success, failure, edge cases, duplicates
- **Async testing**: Flask test client for endpoint testing
- **Pytest fixtures**: Reusable test data and setup/teardown

### Extension Permissions
- **Manifest v3** with explicit localhost permissions
- **Content scripts** only on CarGurus domains
- **CORS headers** required for cross-origin requests to localhost

## Current File Structure

```
gti-listings/
├── app.py                 # Main Flask application (33 lines)
├── config.py              # Configuration and logging setup
├── store.py               # Data storage and VIN deduplication
├── listing_utils.py       # Data comparison and merging utilities
├── routes/                # Route handlers by functionality
│   ├── __init__.py
│   ├── listings.py        # Main listing page and POST endpoint
│   ├── individual.py      # Individual listing detail pages
│   └── health.py          # Health check endpoint
├── templates/             # Jinja2 templates
│   ├── base.html          # Common layout and styling
│   ├── index.html         # Main listings page
│   └── listing_detail.html # Individual listing detail page
├── gti-extension/         # Browser extension
│   ├── manifest.json
│   ├── content.js
│   └── popup.html
├── test_app.py            # Flask endpoints tests (16 tests)
├── test_store.py          # Store class tests (10 tests)
├── test_listing_utils.py  # Utility tests (11 tests)
├── data/                  # JSON file storage (gitignored)
├── app.log                # Application logs (gitignored)
└── CLAUDE.md              # This documentation file
```

This modular architecture supports confident iteration and feature expansion while maintaining data integrity, user experience quality, and code maintainability.