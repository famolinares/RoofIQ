from datetime import UTC, datetime
from pathlib import Path
import re


def build_import_table_name(filename: str) -> str:
    """Build a safe SQLite table name for a workbook import."""
    stem = Path(filename).stem.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    safe_name = normalized or "workbook"
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"import_{safe_name}_{timestamp}"
