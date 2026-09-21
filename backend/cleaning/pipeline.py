import pandas as pd

from backend.cleaning.outliers import remove_iqr_outliers
from backend.cleaning.duplicates import remove_duplicates
from backend.cleaning.missing_values import (
    fill_missing_with_median,
    fill_missing_with_mode,
)
from backend.cleaning.standardization import standardize_categories


def clean_dataset(
    df: pd.DataFrame,
    median_columns: list[str] | None = None,
    mode_columns: list[str] | None = None,
    standardize_columns: list[str] | None = None,
    outlier_columns: list[str] | None = None,
    remove_duplicate_rows: bool = False,
    remove_outliers: bool = False,
) -> tuple[pd.DataFrame, dict]:
    """
    Apply selected cleaning operations and return
    the cleaned DataFrame with an audit trail.
    """

    cleaned_df = df.copy()

    audit = {
        "missing_values": {},
        "duplicates_removed": 0,
        "outliers_removed": 0,
        "standardized_columns": [],
    }

    # --------------------------------------------------
    # 1. Remove duplicate rows
    # --------------------------------------------------

    if remove_duplicate_rows:
        rows_before = len(cleaned_df)

        cleaned_df = remove_duplicates(cleaned_df)

        audit["duplicates_removed"] = (
            rows_before - len(cleaned_df)
        )

    # --------------------------------------------------
    # 2. Remove IQR outliers
    # --------------------------------------------------

    if remove_outliers:
        if not outlier_columns:
            raise ValueError(
                "outlier_columns must be provided when "
                "remove_outliers is True."
            )

        rows_before = len(cleaned_df)

        cleaned_df = remove_iqr_outliers(
            cleaned_df,
            outlier_columns,
        )

        audit["outliers_removed"] = (
            rows_before - len(cleaned_df)
        )

    # --------------------------------------------------
    # 3. Median imputation
    # --------------------------------------------------

    if median_columns:
        cleaned_df, missing_audit = fill_missing_with_median(
            cleaned_df,
            median_columns,
        )

        audit["missing_values"].update(missing_audit)

    # --------------------------------------------------
    # 4. Mode imputation
    # --------------------------------------------------

    if mode_columns:
        cleaned_df, mode_audit = fill_missing_with_mode(
            cleaned_df,
            mode_columns,
        )

        audit["missing_values"].update(mode_audit)

    # --------------------------------------------------
    # 5. Standardization
    # --------------------------------------------------

    if standardize_columns:
        cleaned_df = standardize_categories(
            cleaned_df,
            standardize_columns,
        )

        audit["standardized_columns"] = standardize_columns

    return cleaned_df, audit