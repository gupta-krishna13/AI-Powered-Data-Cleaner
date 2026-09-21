import pandas as pd


def remove_iqr_outliers(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Remove rows containing IQR-based outliers
    from the selected numerical columns.
    """

    cleaned_df = df.copy()

    for column in columns:
        if column not in cleaned_df.columns:
            raise ValueError(f"Column not found: {column}")

        if not pd.api.types.is_numeric_dtype(cleaned_df[column]):
            raise TypeError(
                f"Column '{column}' must be numerical "
                "to detect IQR outliers."
            )

        series = cleaned_df[column].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        cleaned_df = cleaned_df[
            (cleaned_df[column].isna()) |
            (
                (cleaned_df[column] >= lower_bound) &
                (cleaned_df[column] <= upper_bound)
            )
        ]

    return cleaned_df