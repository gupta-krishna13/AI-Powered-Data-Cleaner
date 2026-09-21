import pandas as pd


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    """
    return pd.read_csv(file_path)