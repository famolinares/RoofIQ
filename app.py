from pathlib import Path

import streamlit as st

from src.database.connection import DatabaseConfig, initialize_database
from src.services.import_service import ImportService
from src.utils.paths import DATA_DIR


APP_TITLE = "RoofIQ"
APP_SUBTITLE = "South Florida Roof Prospecting Platform"
DATABASE_PATH = DATA_DIR / "roofiq.sqlite3"
RECORD_METRIC_COLUMN_WEIGHT = 1
COLUMN_LIST_COLUMN_WEIGHT = 3


def configure_page() -> None:
    """Configure the Streamlit page shell."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="RoofIQ",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_header() -> None:
    """Render the application title and Phase 1 context."""
    st.title(APP_TITLE)
    st.subheader(APP_SUBTITLE)
    st.caption("Phase 1: spreadsheet intake and structured local storage.")


def render_upload(import_service: ImportService) -> None:
    """Render the Excel upload workflow and imported dataset preview."""
    uploaded_file = st.file_uploader(
        "Upload residential roofing prospect spreadsheet",
        type=["xlsx"],
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.info("Upload an Excel workbook to preview and store prospect data.")
        return

    try:
        imported_dataset = import_service.import_excel(uploaded_file)
    except ValueError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.exception(exc)
        return

    st.success(
        f"Imported {imported_dataset.record_count:,} records into SQLite table "
        f"`{imported_dataset.table_name}`."
    )

    metric_col, table_col = st.columns(
        [RECORD_METRIC_COLUMN_WEIGHT, COLUMN_LIST_COLUMN_WEIGHT]
    )
    with metric_col:
        st.metric("Records", f"{imported_dataset.record_count:,}")
    with table_col:
        st.write("Columns")
        st.dataframe(
            imported_dataset.columns_frame,
            hide_index=True,
            use_container_width=True,
        )

    st.write("First 20 Rows")
    st.dataframe(imported_dataset.preview, use_container_width=True)


def main() -> None:
    """Start the RoofIQ Streamlit application."""
    configure_page()
    render_header()

    database_config = DatabaseConfig(path=Path(DATABASE_PATH))
    initialize_database(database_config)
    import_service = ImportService(database_config=database_config)

    render_upload(import_service)


if __name__ == "__main__":
    main()
