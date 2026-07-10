# RoofIQ Engineering Rules

## Mission

RoofIQ is a residential roofing prospecting platform for South Florida.

The objective is to identify the highest-probability roofing opportunities using property records, permit history, GIS mapping, aerial imagery, and later AI-assisted roof-condition analysis.

## General Principles

* Build production-quality software.
* Prefer readability over cleverness.
* Keep modules small and reusable.
* Never duplicate business logic.
* Keep UI separate from services.
* Keep services separate from database access.
* Every feature must be testable.

## Data Rules

* Never modify the original imported spreadsheet.
* Preserve leading zeros in Folio, Parcel ID, ZIP Code, and every identifier.
* Imported property data is read-only.
* Never commit homeowner spreadsheets to GitHub.
* Never commit SQLite databases.
* Never commit API keys or secrets.

## Development Order

Phase 1

* Import Engine

Phase 2

* Owner Occupancy Detection

Phase 3

* Property Qualification Engine

Phase 4

* GIS Mapping

Phase 5

* Aerial Imagery Integration

Phase 6

* Roof Review Interface

Phase 7

* AI Roof Condition Scoring

Phase 8

* Direct Mail Campaign Engine

Phase 9

* CRM Integration

Do not skip phases unless explicitly instructed.

## Coding Standards

* Python 3.12
* Type hints everywhere.
* Docstrings on public functions.
* No magic numbers.
* Meaningful variable names.
* Use pathlib instead of string paths.
* Use UTC timestamps.
* Handle every exception gracefully.

## Testing Rules

Every new feature must include automated tests.

Never merge code that cannot be tested.

## Git Rules

Small commits.

Meaningful commit messages.

Do not rewrite history.

## Security

Assume the repository is public.

Protect homeowner information.

Protect credentials.

## Performance

Design for at least:

* Miami-Dade
* Broward
* Palm Beach

approximately 300,000 residential properties.

Future expansion must not require architectural changes.
