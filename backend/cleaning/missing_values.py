import pandas as pd


def fill_missing_with_median(
    df: pd.DataFrame,
    columns: list[str],
) -> tuple[pd.DataFrame, dict]:
    """
    Fill missing values in numerical columns using the median
    and return an audit summary.
    """

    cleaned_df = df.copy()
    audit = {}

    for column in columns:
        if column not in cleaned_df.columns:
            raise ValueError(f"Column not found: {column}")

        if not pd.api.types.is_numeric_dtype(cleaned_df[column]):
            raise TypeError(
                f"Column '{column}' must be numerical "
                "to use median imputation."
            )

        missing_before = int(cleaned_df[column].isna().sum())

        cleaned_df[column] = cleaned_df[column].fillna(
            cleaned_df[column].median()
        )

        missing_after = int(cleaned_df[column].isna().sum())

        audit[column] = {
            "missing_before": missing_before,
            "missing_after": missing_after,
            "filled": missing_before - missing_after,
        }

    return cleaned_df, audit

def fill_missing_with_mode(
    df: pd.DataFrame,
    columns: list[str],
) -> tuple[pd.DataFrame, dict]:
    """
    Fill missing values in categorical columns using the mode
    and return an audit summary.
    """

    cleaned_df = df.copy()
    audit = {}

    for column in columns:
        if column not in cleaned_df.columns:
            raise ValueError(f"Column not found: {column}")

        if not pd.api.types.is_object_dtype(cleaned_df[column]):
            raise TypeError(
                f"Column '{column}' must contain categorical/text data "
                "to use mode imputation."
            )

        missing_before = int(cleaned_df[column].isna().sum())

        mode_values = cleaned_df[column].mode()

        if mode_values.empty:
            raise ValueError(
                f"Cannot determine mode for column '{column}'."
            )

        mode_value = mode_values.iloc[0]

        cleaned_df[column] = cleaned_df[column].fillna(mode_value)

        missing_after = int(cleaned_df[column].isna().sum())

        audit[column] = {
            "missing_before": missing_before,
            "missing_after": missing_after,
            "filled": missing_before - missing_after,
            "fill_value": mode_value,
        }

    return cleaned_df, audit