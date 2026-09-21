import pandas as pd

from backend.cleaning.request import CleaningRequest


def validate_cleaning_request(
    df: pd.DataFrame,
    request: CleaningRequest,
) -> None:
    """
    Validate that all requested columns exist
    and are compatible with their cleaning operations.
    """

    # Check whether requested columns exist
    requested_columns = (
        request.median_columns
        + request.mode_columns
        + request.standardize_columns
        + request.outlier_columns
    )

    missing_columns = [
        column
        for column in requested_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Columns not found in dataset: {missing_columns}"
        )

    # Validate median columns
    invalid_median_columns = [
        column
        for column in request.median_columns
        if not pd.api.types.is_numeric_dtype(df[column])
    ]

    if invalid_median_columns:
        raise TypeError(
            "Median imputation requires numerical columns. "
            f"Invalid columns: {invalid_median_columns}"
        )

    # Validate mode columns
    invalid_mode_columns = [
        column
        for column in request.mode_columns
        if not pd.api.types.is_object_dtype(df[column])
    ]

    if invalid_mode_columns:
        raise TypeError(
            "Mode imputation requires text/object columns. "
            f"Invalid columns: {invalid_mode_columns}"
        )

    # Validate standardization columns
    invalid_standardize_columns = [
        column
        for column in request.standardize_columns
        if not pd.api.types.is_object_dtype(df[column])
    ]

    if invalid_standardize_columns:
        raise TypeError(
            "Standardization requires text/object columns. "
            f"Invalid columns: {invalid_standardize_columns}"
        )

    # Validate outlier columns
    invalid_outlier_columns = [
        column
        for column in request.outlier_columns
        if not pd.api.types.is_numeric_dtype(df[column])
    ]

    if invalid_outlier_columns:
        raise TypeError(
            "Outlier detection requires numerical columns. "
            f"Invalid columns: {invalid_outlier_columns}"
        )