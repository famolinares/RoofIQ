# RoofIQ

South Florida Roof Prospecting Platform

RoofIQ is a Streamlit application for residential roofing prospecting. Phase 1 focuses on a professional project foundation, Excel intake, spreadsheet preview, and temporary SQLite storage.

AI roof analysis is intentionally out of scope for Phase 1.

## Features

- Streamlit dashboard titled RoofIQ.
- Excel `.xlsx` upload.
- Spreadsheet loading with Pandas and OpenPyXL.
- Imported record count, column list, and first 20 rows.
- Temporary SQLite persistence for imported datasets.
- Clean module boundaries for future database, model, service, utility, and page additions.

## Project Structure

```text
.
|-- app.py
|-- data/
|-- docs/
|-- exports/
|-- requirements.txt
|-- src/
|   |-- database/
|   |-- models/
|   |-- pages/
|   |-- services/
|   `-- utils/
`-- uploads/
```

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Data Storage

Uploaded workbook data is stored in `data/roofiq.sqlite3`. Each upload is written to a generated import table and tracked in the `import_batches` metadata table.

The SQLite database is temporary for early development and is ignored by Git.
