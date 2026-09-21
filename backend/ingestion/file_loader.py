from pathlib import Path

import pandas as pd

from backend.ingestion.csv_loader import load_csv
from backend.ingestion.excel_loader import load_excel


def load_file(file_path: str) -> pd.DataFrame:
    """
    Load a supported data file into a pandas DataFrame.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    if extension == ".csv":
        return load_csv(file_path)

    if extension in [".xlsx", ".xls"]:
        return load_excel(file_path)

    raise ValueError(
        f"Unsupported file type: {extension}. "
        "Supported formats are CSV and Excel."
    )