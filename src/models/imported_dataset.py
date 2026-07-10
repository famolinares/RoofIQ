from dataclasses import dataclass

import pandas as pd


PREVIEW_ROW_COUNT = 20


@dataclass(frozen=True)
class ImportedDataset:
    """Spreadsheet data and metadata from a completed import."""

    table_name: str
    source_filename: str
    data: pd.DataFrame

    @property
    def record_count(self) -> int:
        """Return the number of imported records."""
        return len(self.data)

    @property
    def preview(self) -> pd.DataFrame:
        """Return the first rows displayed in the Phase 1 dashboard."""
        return self.data.head(PREVIEW_ROW_COUNT)

    @property
    def columns_frame(self) -> pd.DataFrame:
        """Return imported column names in a display-friendly dataframe."""
        return pd.DataFrame({"Column Name": list(self.data.columns)})
