from datetime import datetime
from pathlib import Path
import re


def build_import_table_name(filename: str) -> str:
    stem = Path(filename).stem.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    safe_name = normalized or "workbook"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"import_{safe_name}_{timestamp}"
