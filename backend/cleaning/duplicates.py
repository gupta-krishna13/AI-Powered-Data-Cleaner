import pandas as pd


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate rows from a DataFrame.
    """
    cleaned_df = df.copy()

    cleaned_df = cleaned_df.drop_duplicates()

    return cleaned_df