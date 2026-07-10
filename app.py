from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler

from src.database.connection import DatabaseConfig, initialize_database
from src.models.imported_dataset import PREVIEW_ROW_COUNT
from src.services.import_service import ImportService
from src.services.occupancy_service import (
    NON_OWNER_OCCUPIED_STATUS,
    OCCUPANCY_STATUS_COLUMN,
    OWNER_OCCUPIED_STATUS,
    UNKNOWN_OCCUPANCY_STATUS,
    OccupancyService,
)
from src.utils.paths import DATA_DIR


APP_TITLE = "RoofIQ"
APP_SUBTITLE = "South Florida Roof Prospecting Platform"
DATABASE_PATH = DATA_DIR / "roofiq.sqlite3"
RECORD_METRIC_COLUMN_WEIGHT = 1
COLUMN_LIST_COLUMN_WEIGHT = 3
OCCUPANCY_METRIC_COLUMN_COUNT = 5
OWNER_OCCUPIED_COLOR = "background-color: #d1fae5; color: #065f46;"
NON_OWNER_OCCUPIED_COLOR = "background-color: #f3f4f6; color: #374151;"
UNKNOWN_OCCUPANCY_COLOR = "background-color: #fef3c7; color: #92400e;"
FILTER_ALL = "All"
FILTER_OWNER_OCCUPIED = "Likely Owner Occupied"
FILTER_NON_OWNER_OCCUPIED = "Likely Non Owner Occupied"
FILTER_UNKNOWN = "Unknown"


def configure_page() -> None:
    """Configure the Streamlit page shell."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="RoofIQ",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_header() -> None:
    """Render the application title and Phase 2 context."""
    st.title(APP_TITLE)
    st.subheader(APP_SUBTITLE)
    st.caption("Phase 2: owner occupancy detection.")


def render_upload(
    import_service: ImportService,
    occupancy_service: OccupancyService,
) -> None:
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

    try:
        classified_data = occupancy_service.classify_dataframe(imported_dataset.data)
    except ValueError as exc:
        st.error(str(exc))
        return

    owner_occupied_count = int(
        (classified_data[OCCUPANCY_STATUS_COLUMN] == OWNER_OCCUPIED_STATUS).sum()
    )
    non_owner_occupied_count = int(
        (classified_data[OCCUPANCY_STATUS_COLUMN] == NON_OWNER_OCCUPIED_STATUS).sum()
    )
    unknown_count = int(
        (classified_data[OCCUPANCY_STATUS_COLUMN] == UNKNOWN_OCCUPANCY_STATUS).sum()
    )
    known_record_count = owner_occupied_count + non_owner_occupied_count
    occupancy_percentage = (
        owner_occupied_count / known_record_count if known_record_count else 0
    )

    st.success(
        f"Imported {imported_dataset.record_count:,} records into SQLite table "
        f"`{imported_dataset.table_name}`."
    )

    total_col, owner_col, non_owner_col, unknown_col, percent_col = st.columns(
        OCCUPANCY_METRIC_COLUMN_COUNT
    )
    with total_col:
        st.metric("Total Records", f"{imported_dataset.record_count:,}")
    with owner_col:
        st.metric("Likely Owner Occupied", f"{owner_occupied_count:,}")
    with non_owner_col:
        st.metric("Likely Non Owner Occupied", f"{non_owner_occupied_count:,}")
    with unknown_col:
        st.metric("Unknown", f"{unknown_count:,}")
    with percent_col:
        st.metric("Occupancy %", f"{occupancy_percentage:.1%}")

    selected_filter = st.selectbox(
        "Occupancy filter",
        [
            FILTER_ALL,
            FILTER_OWNER_OCCUPIED,
            FILTER_NON_OWNER_OCCUPIED,
            FILTER_UNKNOWN,
        ],
    )
    display_data = filter_occupancy_data(classified_data, selected_filter)

    record_col, table_col = st.columns(
        [RECORD_METRIC_COLUMN_WEIGHT, COLUMN_LIST_COLUMN_WEIGHT]
    )
    with record_col:
        st.metric("Displayed Records", f"{len(display_data):,}")
    with table_col:
        st.write("Columns")
        st.dataframe(
            classified_data.columns.to_frame(index=False, name="Column Name"),
            hide_index=True,
            use_container_width=True,
        )

    st.write("First 20 Rows")
    st.dataframe(
        style_occupancy_status(display_data.head(PREVIEW_ROW_COUNT)),
        use_container_width=True,
    )


def style_occupancy_status(data_frame: pd.DataFrame) -> Styler:
    """Color the occupancy status column for Streamlit display."""

    def style_cell(value: str) -> str:
        if value == OWNER_OCCUPIED_STATUS:
            return OWNER_OCCUPIED_COLOR
        if value == NON_OWNER_OCCUPIED_STATUS:
            return NON_OWNER_OCCUPIED_COLOR
        if value == UNKNOWN_OCCUPANCY_STATUS:
            return UNKNOWN_OCCUPANCY_COLOR
        return ""

    return data_frame.style.map(style_cell, subset=[OCCUPANCY_STATUS_COLUMN])


def filter_occupancy_data(
    data_frame: pd.DataFrame,
    selected_filter: str,
) -> pd.DataFrame:
    """Filter classified records by the selected occupancy status."""
    if selected_filter == FILTER_OWNER_OCCUPIED:
        return data_frame[data_frame[OCCUPANCY_STATUS_COLUMN] == OWNER_OCCUPIED_STATUS]
    if selected_filter == FILTER_NON_OWNER_OCCUPIED:
        return data_frame[
            data_frame[OCCUPANCY_STATUS_COLUMN] == NON_OWNER_OCCUPIED_STATUS
        ]
    if selected_filter == FILTER_UNKNOWN:
        return data_frame[
            data_frame[OCCUPANCY_STATUS_COLUMN] == UNKNOWN_OCCUPANCY_STATUS
        ]
    return data_frame


def main() -> None:
    """Start the RoofIQ Streamlit application."""
    configure_page()
    render_header()

    database_config = DatabaseConfig(path=Path(DATABASE_PATH))
    initialize_database(database_config)
    import_service = ImportService(database_config=database_config)
    occupancy_service = OccupancyService()

    render_upload(import_service, occupancy_service)


if __name__ == "__main__":
    main()
