from backend.ai.decision import RecommendationDecision
from backend.ai.proposal import CleaningProposal
from backend.cleaning.request import CleaningRequest


def proposal_to_cleaning_request(
    proposal: CleaningProposal,
    decisions: list[RecommendationDecision],
) -> CleaningRequest:
    """
    Convert only the user-selected recommendations
    into a deterministic CleaningRequest.
    """

    median_columns = []
    mode_columns = []
    standardize_columns = []
    outlier_columns = []

    remove_duplicate_rows = False
    remove_outliers = False

    decision_map = {
        decision.recommendation_index: decision.decision
        for decision in decisions
    }

    for index, recommendation in enumerate(
        proposal.recommendations
    ):

        decision = decision_map.get(index)

        # -------------------------------------------------
        # No executable decision
        # -------------------------------------------------

        if decision in {
            None,
            "reject",
            "keep",
        }:

            continue

        # -------------------------------------------------
        # Median imputation
        # -------------------------------------------------

        if (
            recommendation.operation
            == "median_imputation"
            and decision == "approve"
        ):

            median_columns.extend(
                recommendation.columns
            )

        # -------------------------------------------------
        # Mode imputation
        # -------------------------------------------------

        elif (
            recommendation.operation
            == "mode_imputation"
            and decision == "approve"
        ):

            mode_columns.extend(
                recommendation.columns
            )

        # -------------------------------------------------
        # Standardization
        # -------------------------------------------------

        elif (
            recommendation.operation
            == "standardization"
            and decision == "approve"
        ):

            standardize_columns.extend(
                recommendation.columns
            )

        # -------------------------------------------------
        # Outlier removal
        # -------------------------------------------------

        elif (
            recommendation.operation
            == "remove_outliers"
            and decision == "remove"
        ):

            outlier_columns.extend(
                recommendation.columns
            )

            remove_outliers = True

        # -------------------------------------------------
        # Duplicate removal
        # -------------------------------------------------

        elif (
            recommendation.operation
            == "remove_duplicates"
            and decision == "remove"
        ):

            remove_duplicate_rows = True

    # -------------------------------------------------
    # Remove duplicate column entries
    # -------------------------------------------------

    median_columns = list(
        dict.fromkeys(median_columns)
    )

    mode_columns = list(
        dict.fromkeys(mode_columns)
    )

    standardize_columns = list(
        dict.fromkeys(standardize_columns)
    )

    outlier_columns = list(
        dict.fromkeys(outlier_columns)
    )

    return CleaningRequest(
        median_columns=median_columns,
        mode_columns=mode_columns,
        standardize_columns=standardize_columns,
        outlier_columns=outlier_columns,
        remove_duplicate_rows=remove_duplicate_rows,
        remove_outliers=remove_outliers,
    )