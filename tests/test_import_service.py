from io import BytesIO
import re
import sqlite3

import pandas as pd
import pytest

from src.database.connection import DatabaseConfig, initialize_database
from src.services.import_service import ImportService
from src.utils.table_names import build_import_table_name


class NamedBytesIO(BytesIO):
    def __init__(self, content: bytes, name: str) -> None:
        super().__init__(content)
        self.name = name


def build_workbook(
    data_frame: pd.DataFrame,
    filename: str = "prospects.xlsx",
) -> NamedBytesIO:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data_frame.to_excel(writer, index=False)
    return NamedBytesIO(buffer.getvalue(), filename)


def build_import_service(tmp_path) -> ImportService:
    database_config = DatabaseConfig(path=tmp_path / "roofiq.sqlite3")
    initialize_database(database_config)
    return ImportService(database_config=database_config)


def test_excel_import_reads_all_records_and_preserves_identifier_text(tmp_path) -> None:
    data_frame = pd.DataFrame(
        {
            "Folio": [f"00012345{i:04d}" for i in range(1000)],
            "Zip_Code": [f"0{33000 + (i % 100):05d}" for i in range(1000)],
            "Owner": [f"Owner {i}" for i in range(1000)],
        }
    )
    service = build_import_service(tmp_path)

    imported_dataset = service.import_excel(build_workbook(data_frame))

    assert imported_dataset.record_count == 1000
    assert imported_dataset.columns_frame["Column Name"].tolist() == [
        "Folio",
        "Zip_Code",
        "Owner",
    ]
    assert len(imported_dataset.preview) == 20
    assert imported_dataset.data.loc[0, "Folio"] == "000123450000"
    assert imported_dataset.data.loc[0, "Zip_Code"].startswith("0")


def test_empty_spreadsheet_is_rejected(tmp_path) -> None:
    empty_workbook = build_workbook(pd.DataFrame(columns=["Folio", "Zip_Code"]))
    service = build_import_service(tmp_path)

    with pytest.raises(ValueError, match="does not contain any records"):
        service.import_excel(empty_workbook)


def test_invalid_file_extension_is_rejected(tmp_path) -> None:
    service = build_import_service(tmp_path)
    invalid_file = NamedBytesIO(b"not an excel workbook", "prospects.csv")

    with pytest.raises(ValueError, match=r"\.xlsx"):
        service.import_excel(invalid_file)


def test_invalid_xlsx_content_is_rejected(tmp_path) -> None:
    service = build_import_service(tmp_path)
    invalid_file = NamedBytesIO(b"not an excel workbook", "prospects.xlsx")

    with pytest.raises(ValueError, match="could not be read"):
        service.import_excel(invalid_file)


def test_safe_sqlite_table_name_generation() -> None:
    table_name = build_import_table_name("../../South Florida Prospects 2026!.xlsx")

    assert table_name.startswith("import_south_florida_prospects_2026_")
    assert re.fullmatch(r"[a-z0-9_]+", table_name)


def test_import_persists_dataset_and_batch_metadata(tmp_path) -> None:
    database_path = tmp_path / "roofiq.sqlite3"
    database_config = DatabaseConfig(path=database_path)
    initialize_database(database_config)
    service = ImportService(database_config=database_config)
    workbook = build_workbook(
        pd.DataFrame(
            {
                "Folio": ["000000000001", "000000000002"],
                "Zip_Code": ["033101", "033102"],
            }
        )
    )

    imported_dataset = service.import_excel(workbook)

    with sqlite3.connect(database_path) as connection:
        imported_rows = connection.execute(
            f"""
            SELECT Folio, Zip_Code
            FROM "{imported_dataset.table_name}"
            ORDER BY Folio;
            """
        ).fetchall()
        batch = connection.execute(
            """
            SELECT source_filename, table_name, record_count, imported_at
            FROM import_batches
            WHERE table_name = ?;
            """,
            (imported_dataset.table_name,),
        ).fetchone()

    assert imported_rows == [
        ("000000000001", "033101"),
        ("000000000002", "033102"),
    ]
    assert batch is not None
    assert batch[0] == "prospects.xlsx"
    assert batch[1] == imported_dataset.table_name
    assert batch[2] == 2
    assert batch[3].endswith("+00:00")
