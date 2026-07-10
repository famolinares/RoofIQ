from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ImportedDataset:
    table_name: str
    source_filename: str
    data: pd.DataFrame

    @property
    def record_count(self) -> int:
        return len(self.data)

    @property
    def preview(self) -> pd.DataFrame:
        return self.data.head(20)

    @property
    def columns_frame(self) -> pd.DataFrame:
        return pd.DataFrame({"Column Name": list(self.data.columns)})
