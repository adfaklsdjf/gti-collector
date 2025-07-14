# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GTI Listings Collector** - A local Flask app with browser extension for collecting and managing used Volkswagen GTI listings from car websites. Emphasizes incremental development, comprehensive testing, and clean architecture.

## Current Architecture

### Backend (Python/Flask)
- **Flask app** (`app.py`) - REST API with CORS support
- **Store class** (`store.py`) - File-based storage with VIN deduplication and upsert logic
- **Listing utilities** (`listing_utils.py`) - Data comparison, merging, and change detection
- **Storage format**: Individual JSON files per listing + VIN index for fast lookups

### Frontend (Browser Extension)
- **Browser extension** (`gti-extension/`) - Chrome/Brave extension for CarGurus.com
- **Content script** (`content.js`) - Extracts listing data, sends to local Flask API
- **Smart toast notifications** - Success/update/no-change feedback to user
- **Robust selectors** - Multiple fallback strategies for brittle generated class names

### Web Interface
- **Listings display** - Responsive card-based layout at `http://127.0.0.1:5000/`
- **Price sorting** - Listings sorted low to high for easy comparison
- **Title and location display** - When available from extraction

## Key Features Working

### Data Collection
- **VIN-based deduplication** with intelligent upsert behavior
- **Title and location extraction** with multiple selector fallbacks
- **Required fields**: url, price, year, mileage, distance, vin
- **Optional fields**: title, location (preserved when available)
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

# Run all tests (32 tests total)
python -m pytest -v

# Run specific test file
python -m pytest test_store.py -v

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
- Current ignored: `*.log`, `__pycache__/`, `data/`, `.pytest_cache/`, `*.pyc`

## Testing Philosophy

**Goal**: Minimize debug loops by catching errors autonomously through comprehensive testing.

### Current Coverage (32 tests)
- **Unit tests**: Store class (8 tests) - VIN deduplication, upserts, file operations
- **Integration tests**: Flask endpoints (13 tests) - API functionality, error handling, CORS
- **Utility tests**: listing_utils module (11 tests) - data comparison, merging, formatting

### Testing Approach
- **Isolated test environments** with temporary directories and cleanup
- **Comprehensive fixtures** for reusable test data
- **Error scenario coverage** - missing fields, invalid data, file system issues
- **pytest configuration** with verbose output and clean tracebacks
- **Add tests when adding features** to maintain safety net

## Development Guidelines

### Incremental Approach
- **Highly incremental development** - small testable steps
- **Avoid doing too much at once** to prevent bugfixing spirals
- **No file should exceed ~100 lines** to maintain simplicity
- **Verify each step before proceeding** to next feature
- **Break complex features into multiple commits**

### Code Organization
- **Modular design** - separate concerns into focused modules
- **Light refactoring** when adding features, not wholesale rewrites
- **Defensive programming** - handle missing directories, network failures, etc.
- **Comprehensive logging** for debugging and monitoring

### Field Management
- **Required vs Optional distinction** is crucial for future expansion
- **Optional fields preserved** when new extraction provides None/empty values
- **Change detection** only triggers on meaningful value differences
- **Extensible field system** ready for additional data types

## Future Expansion Areas

### Additional Fields
- **Simple fields first** (dealer info, listing age, trim levels)
- **Complex fields later** (images, detailed specs, package detection)
- **User-edited fields** (notes, favorites, manual annotations)

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
- **Filtering and sorting** options
- **Export functionality** (CSV, spreadsheets)
- **Image previews** when available
- **Advanced search and comparison** tools
- **User management** for multi-user scenarios

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
    "distance": "string (required)",
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

This architecture supports confident iteration and feature expansion while maintaining data integrity and user experience quality.