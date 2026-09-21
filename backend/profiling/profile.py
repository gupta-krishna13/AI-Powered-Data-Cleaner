import pandas as pd


def profile_dataset(df: pd.DataFrame) -> dict:
    """
    Generate a basic profile of a pandas DataFrame.
    """

    numerical_columns = df.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    missing_values = df.isnull().sum()

    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_names": df.columns.tolist(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": missing_values[missing_values > 0].to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "numerical_columns": numerical_columns,
        "categorical_columns": categorical_columns,
    }