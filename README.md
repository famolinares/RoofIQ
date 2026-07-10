# RoofIQ

RoofIQ is a South Florida roof-prospecting application that combines county property records, owner-occupancy signals, permit-age filters, aerial imagery, and later AI-assisted roof-condition scoring.

## Current milestone

Version 0.1 provides a working local data-review application that:

- imports the Miami-Dade enriched CSV/XLSX file;
- preserves folio numbers as text;
- identifies likely owner-occupied properties by comparing situs and mailing addresses;
- filters by market tier, ZIP code, roof age, property value, and occupancy status;
- displays prospect-level property and owner details;
- exports a filtered postcard-mailing CSV;
- keeps homeowner data out of GitHub.

## Run locally

1. Install Python 3.11 or newer.
2. Clone this repository.
3. Create and activate a virtual environment.
4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Start the application:

```bash
streamlit run app.py
```

6. Upload `Miami_Dade_1665_Enriched.xlsx` or a compatible CSV/XLSX file through the application.

## Data privacy

Do **not** commit property-owner files, mailing lists, aerial-image exports, API keys, or credentials to this repository. The repository is currently public. Uploaded files are processed during the local Streamlit session and are not written to the repository.

## Required Miami-Dade fields

The first release recognizes the following columns from the supplied enriched sample:

- `Folio_Accurate`
- `Address`
- `Zip_Code`
- `Year_Built`
- `Roof_Age_Years`
- `Owner_Name_Primary`
- `Owner_Name_Secondary`
- `Market_Tier`
- `CO_Property City`
- `CO_Total`
- `CO_Assessed`
- `CO_Land Use`
- `CO_Owner1`
- `CO_Owner2`
- `CO_Mailing Address`
- `CO_Mailing City`
- `CO_Mailing State`
- `CO_Mailing Zip`

## Roadmap

1. Local import, qualification, review, and mailing export.
2. Geocoding and interactive parcel map.
3. Licensed aerial-imagery adapter.
4. Manual roof-review labels and audit trail.
5. AI-assisted roof-condition prioritization.
6. Broward and Palm Beach import adapters.
