from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import BinaryIO

import pandas as pd

from src.database.connection import DatabaseConfig, get_connection
from src.models.imported_dataset import ImportedDataset
from src.utils.table_names import build_import_table_name


@dataclass(frozen=True)
class ImportService:
    """Application service for importing Excel workbooks into SQLite."""

    database_config: DatabaseConfig

    def import_excel(self, uploaded_file: BinaryIO) -> ImportedDataset:
        """Read, validate, persist, and summarize an uploaded Excel workbook."""
        source_filename = getattr(uploaded_file, "name", "uploaded_workbook.xlsx")
        if not source_filename.lower().endswith(".xlsx"):
            raise ValueError("Please upload a valid .xlsx Excel workbook.")

        try:
            data_frame = pd.read_excel(
                uploaded_file,
                engine="openpyxl",
                dtype=str,
                keep_default_na=False,
            )
        except Exception as exc:
            raise ValueError(
                "The uploaded workbook could not be read as a valid .xlsx file."
            ) from exc

        if data_frame.empty:
            raise ValueError("The uploaded workbook does not contain any records.")

        table_name = build_import_table_name(source_filename)
        self._store_import(source_filename, table_name, data_frame)

        return ImportedDataset(
            table_name=table_name,
            source_filename=source_filename,
            data=data_frame,
        )

    def _store_import(
        self,
        source_filename: str,
        table_name: str,
        data_frame: pd.DataFrame,
    ) -> None:
        with get_connection(self.database_config) as connection:
            data_frame.to_sql(table_name, connection, if_exists="replace", index=False)
            connection.execute(
                """
                INSERT INTO import_batches (
                    source_filename,
                    table_name,
                    record_count,
                    imported_at
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    source_filename,
                    table_name,
                    len(data_frame),
                    datetime.now(UTC).isoformat(),
                ),
            )
