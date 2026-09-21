import pandas as pd

from backend.ai.proposal import CleaningProposal


SUPPORTED_OPERATIONS = {
    "median_imputation",
    "mode_imputation",
    "standardization",
    "remove_outliers",
    "remove_duplicates",
}


def validate_proposal_operations(
    proposal: CleaningProposal,
) -> None:
    """
    Validate that every recommendation uses
    a supported cleaning operation.
    """

    invalid_operations = [
        recommendation.operation
        for recommendation in proposal.recommendations
        if recommendation.operation not in SUPPORTED_OPERATIONS
    ]

    if invalid_operations:
        raise ValueError(
            f"Unsupported cleaning operations: {invalid_operations}"
        )


def validate_proposal_columns(
    df: pd.DataFrame,
    proposal: CleaningProposal,
) -> None:
    """
    Validate that all columns recommended by the AI
    exist in the dataset.
    """

    invalid_columns = []

    for recommendation in proposal.recommendations:
        for column in recommendation.columns:
            if column not in df.columns:
                invalid_columns.append(column)

    if invalid_columns:
        raise ValueError(
            f"Columns not found in dataset: {invalid_columns}"
        )
        
def validate_proposal_compatibility(
    df: pd.DataFrame,
    proposal: CleaningProposal,
) -> None:
    """
    Validate that recommended columns are compatible
    with their cleaning operations.
    """

    for recommendation in proposal.recommendations:

        if recommendation.operation == "median_imputation":
            invalid_columns = [
                column
                for column in recommendation.columns
                if not pd.api.types.is_numeric_dtype(df[column])
            ]

            if invalid_columns:
                raise TypeError(
                    "Median imputation requires numerical columns. "
                    f"Invalid columns: {invalid_columns}"
                )

        elif recommendation.operation == "standardization":
            invalid_columns = [
                column
                for column in recommendation.columns
                if not pd.api.types.is_object_dtype(df[column])
            ]

            if invalid_columns:
                raise TypeError(
                    "Standardization requires text/object columns. "
                    f"Invalid columns: {invalid_columns}"
                )

        elif recommendation.operation == "remove_outliers":
            invalid_columns = [
                column
                for column in recommendation.columns
                if not pd.api.types.is_numeric_dtype(df[column])
            ]

            if invalid_columns:
                raise TypeError(
                    "Outlier removal requires numerical columns. "
                    f"Invalid columns: {invalid_columns}"
                )
                
def validate_proposal_reasons(
    proposal: CleaningProposal,
) -> None:
    """
    Validate that every recommendation contains
    a meaningful reason.
    """

    for recommendation in proposal.recommendations:
        if not recommendation.reason.strip():
            raise ValueError(
                f"Recommendation for operation "
                f"'{recommendation.operation}' must contain a reason."
            )
            
OPERATION_TO_REQUEST_FIELD = {
    "median_imputation": "median_columns",
    "mode_imputation": "mode_columns",
    "standardization": "standardize_columns",
    "remove_outliers": "outlier_columns",
    "remove_duplicates": "remove_duplicate_rows",
}