from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

import pandas as pd

from src.database.connection import DatabaseConfig, get_connection
from src.models.imported_dataset import ImportedDataset
from src.utils.table_names import build_import_table_name


@dataclass(frozen=True)
class ImportService:
    database_config: DatabaseConfig

    def import_excel(self, uploaded_file: BinaryIO) -> ImportedDataset:
        source_filename = getattr(uploaded_file, "name", "uploaded_workbook.xlsx")
        if not source_filename.lower().endswith(".xlsx"):
            raise ValueError("Please upload a valid .xlsx Excel workbook.")

        data_frame = pd.read_excel(uploaded_file, engine="openpyxl")
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
                    record_count
                )
                VALUES (?, ?, ?);
                """,
                (source_filename, table_name, len(data_frame)),
            )
