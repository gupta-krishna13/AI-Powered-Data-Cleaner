import pandas as pd


def generate_cleaning_report(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    audit: dict,
) -> dict:
    """
    Generate a cleaning report using the actual
    operations recorded in the audit trail.
    """

    return {
        "rows_before": len(original_df),
        "rows_after": len(cleaned_df),
        "rows_removed": len(original_df) - len(cleaned_df),
        "columns_before": len(original_df.columns),
        "columns_after": len(cleaned_df.columns),
        "missing_values": audit["missing_values"],
        "duplicates_removed": audit["duplicates_removed"],
        "outliers_removed": audit["outliers_removed"],
        "standardized_columns": audit["standardized_columns"],
    }