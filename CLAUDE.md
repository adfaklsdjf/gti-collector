# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**CRITICAL**: After context compaction, Claude MUST re-read this file first to refresh project understanding and current guidelines.

**ESSENTIAL**: Before starting any task, consider if there are questions/clarifications that would be helpful and pro-actively ask them. Don't assume - ask about scope, preferences, constraints, or implementation details that could affect the approach.

## Project Overview

**GTI Listings Collector** - A local Flask app with browser extension for collecting and managing used Volkswagen GTI listings from car websites. Emphasizes incremental development, comprehensive testing, and clean architecture.

## Current Architecture

### Backend Components
- **Flask app** (`app.py`) - Main application with modular routes and pre-flight migration checks
- **PID lock system** (`pidlock.py`) - Single-instance enforcement with graceful signal handling
- **Schema migration system** (`schema_migrations.py`) - Drupal-style versioned migrations with per-file tracking
- **Multi-site support** (`site_mappings.py`) - Site detection and field mapping
- **Store class** (`store.py`) - VIN-based deduplication with just-in-time migration support
- **Desirability scoring** (`desirability.py`) - Multi-criteria ranking algorithm

### Frontend & Extension
- **Browser extension** (`gti-extension/`) - Multi-site car listing extraction
- **Web interface** - Responsive listings display with sorting and individual detail pages
- **Template system** - Jinja2 inheritance for maintainable UI

### Data Architecture
- **Schema versioning** - Per-file version tracking with sequential migration support
- **Multi-site URLs** - Each listing tracks URLs from multiple car sites
- **VIN deduplication** - Merge data across sites using VIN as primary key
- **Individual JSON files** - One file per listing with schema-versioned VIN index

## Core Features

### Multi-Site Data Collection
- **VIN-based deduplication** - Merges data across CarGurus, AutoTrader, Cars.com
- **Automatic distance extraction** - From location text like "City, State (123 mi away)"
- **Field mapping system** - Handles site-specific data variations
- **Change detection** - Only updates when meaningful data changes

### Desirability Scoring
- **Weighted normalization** (0-100 scale): Price 40%, Mileage 30%, Year 20%, Distance 10%
- **Real-time calculation** - Scores update with current data context
- **Visual rankings** - Star ratings on listing cards with dual sort options

### Schema Migration System
- **Drupal-style versioning** - Sequential migrations with per-file version tracking
- **Pre-flight checks** - App startup migration for bulk operations (index-first optimization)
- **Just-in-time migration** - Runtime file-level migration with warnings
- **Automatic backups** - Timestamped tarballs before bulk migrations
- **Implicit versioning** - Current schema = highest available migration number
- **Historical preservation** - All migration code preserved in migrations/ directory

### Next Priorities
- **Multi-site extraction** - Add AutoTrader and Cars.com selectors to extension
- **Qualitative scoring factors** - Accident penalties, title bonuses, owner count penalties
- **User preferences** - Configurable weights and trim level preferences

## Development Workflow

### Essential Commands (ALWAYS activate venv first)
```bash
# Start Flask app (auto-reloads on changes with pre-flight migration check)
source venv/bin/activate && python app.py

# Run all tests
source venv/bin/activate && python -m pytest -v

# Schema migration commands
source venv/bin/activate && python schema_migrations.py check
source venv/bin/activate && python schema_migrations.py preflight
source venv/bin/activate && python schema_migrations.py list-migrations
```

### Single Instance & Process Management
- **PID lock enforcement** - Prevents multiple app instances running simultaneously
- **Flask debug mode handling** - Detects reloader process and skips PID lock for parent process
- **Graceful signal handling** - SIGINT (Ctrl+C) and SIGTERM trigger proper shutdown
- **Process safety checks** - Validates existing processes before startup
- **Automatic cleanup** - PID files removed on normal or signal-triggered shutdown

### Development Workflow
1. **Test-driven development** - Add tests for new features
2. **Incremental changes** - Small, focused commits
3. **Git commits** - Always commit completed tasks with "🤖 Generated with Claude Code" footer

## Testing Strategy

**Goal**: Comprehensive test coverage to minimize debug loops. Currently 83+ tests covering unit, integration, and migration scenarios.

**Key principle**: Add tests when adding features to maintain safety net.

## Context Management

### After Context Compaction
- **FIRST STEP**: Re-read CLAUDE.md to refresh understanding
- **NEXT**: Review recent commits and current file structure 
- **THEN**: Begin task with strategic file reading and tool use

## Development Guidelines

- **Incremental approach** - Small, testable steps with focused commits
- **Modular design** - Clear separation of concerns across files
- **Defensive programming** - Handle missing directories, network failures, etc.
- **Field management** - Preserve optional fields, detect meaningful changes only

## Current Data Schema (v2)

### Listing File Structure
```json
{
  "schema_version": 2,
  "id": "uuid",
  "data": {
    "urls": {"cargurus": "url", "autotrader": "url"},
    "last_updated_site": "cargurus",
    "sites_seen": ["cargurus", "autotrader"],
    "price": "string", "year": "string", "mileage": "string", "vin": "string",
    "distance": "numeric string", "title": "string", "location": "string",
    "trim_level": "string", "accidents": "string", "previous_owners": "string"
  },
  "comments": "user-editable text"
}
```

### Index File Structure  
```json
{
  "schema_version": 2,
  "vin_mappings": {
    "VIN123": "listing-id-456",
    "VIN789": "listing-id-012"
  }
}
```

## Technical Notes

### CarGurus Extraction Patterns
- **Selectors**: `data-cg-ft="vdp-listing-title"`, multiple fallbacks for brittle class names
- **Distance extraction**: From location text like "Cleveland, OH (15 mi away)"

### Extension Requirements  
- **Manifest v3** with localhost permissions for CORS requests

## File Structure

```
gti-listings/
├── app.py, config.py, store.py          # Core Flask app and storage
├── pidlock.py                           # Single-instance PID lock management
├── schema_migrations.py                 # Schema versioning migration system
├── migrations/                          # Versioned migration files (v001, v002, etc.)
├── desirability.py, site_mappings.py    # Scoring and multi-site support
├── routes/                              # Route handlers
├── templates/                           # Jinja2 templates
├── gti-extension/                       # Browser extension
├── test_*.py                            # Comprehensive test suite
├── requirements.txt                     # Python dependencies (includes psutil)
├── data/                                # JSON listings (gitignored)
├── backups/                             # Migration backups (gitignored)
├── gti-listings.pid                     # PID lock file (gitignored, auto-cleaned)
└── CLAUDE.md                            # This documentation
```

**REMEMBER**: Always read CLAUDE.md first after context compaction, then ask clarifying questions before starting tasks.
