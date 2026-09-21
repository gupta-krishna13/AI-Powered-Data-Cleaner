from backend.ai.proposal import (
    CleaningProposal,
    CleaningRecommendation,
)


def generate_rule_based_proposal(
    ai_input: dict,
) -> CleaningProposal:
    """
    Generate a conservative cleaning proposal using
    deterministic rules based on detected data-quality issues.

    The detector identifies problems.
    This layer interprets those problems and creates
    recommendations without automatically assuming
    that every issue should be removed or modified.
    """

    recommendations = []

    missing_values = ai_input[
        "quality_issues"
    ]["missing_values"]

    numerical_columns = set(
        ai_input["profile"]["numerical_columns"]
    )

    categorical_columns = set(
        ai_input["profile"]["categorical_columns"]
    )

    # -------------------------------------------------
    # Missing values
    # -------------------------------------------------

    for column, missing_count in missing_values.items():

        if column in numerical_columns:

            recommendations.append(
                CleaningRecommendation(
                    issue_type="missing_values",
                    operation="median_imputation",
                    columns=[column],
                    affected_values=[],
                    detection_method="Missing-value detection",
                    evidence=(
                        f"Column '{column}' contains "
                        f"{missing_count} missing numerical value(s)."
                    ),
                    interpretation=(
                        "Missing numerical values may affect "
                        "analysis and downstream processing."
                    ),
                    recommended_action="impute",
                    confidence="high",
                    reason=(
                        f"Median imputation is proposed for "
                        f"missing numerical values in '{column}'. "
                        "The median is less sensitive to extreme "
                        "values than the mean."
                    ),
                )
            )

        elif column in categorical_columns:

            recommendations.append(
                CleaningRecommendation(
                    issue_type="missing_values",
                    operation="mode_imputation",
                    columns=[column],
                    affected_values=[],
                    detection_method="Missing-value detection",
                    evidence=(
                        f"Column '{column}' contains "
                        f"{missing_count} missing categorical value(s)."
                    ),
                    interpretation=(
                        "Missing categorical values may affect "
                        "grouping, filtering, and analysis."
                    ),
                    recommended_action="impute",
                    confidence="medium",
                    reason=(
                        f"Mode imputation is proposed for "
                        f"missing categorical values in '{column}'. "
                        "The most frequent observed category can "
                        "be used as a candidate replacement."
                    ),
                )
            )

    # -------------------------------------------------
    # Duplicate rows
    # -------------------------------------------------

    duplicate_rows = ai_input[
        "quality_issues"
    ]["duplicate_rows"]

    if duplicate_rows > 0:

        recommendations.append(
            CleaningRecommendation(
                issue_type="duplicate_rows",
                operation="remove_duplicates",
                columns=[],
                affected_values=[],
                detection_method="Exact row comparison",
                evidence=(
                    f"The dataset contains {duplicate_rows} "
                    "exact duplicate row(s)."
                ),
                interpretation=(
                    "Identical rows may represent duplicated "
                    "records, although identical transactions "
                    "can also be legitimate in some datasets."
                ),
                recommended_action="review",
                confidence="high",
                reason=(
                    "The duplicate rows should be reviewed before "
                    "removal because identical records are not "
                    "necessarily erroneous in every dataset."
                ),
            )
        )

    # -------------------------------------------------
    # Inconsistent categorical values
    # -------------------------------------------------

    inconsistent_categories = ai_input[
        "quality_issues"
    ]["inconsistent_categories"]

    for column, inconsistency in (
        inconsistent_categories.items()
    ):

        if inconsistency["detected"]:

            groups = inconsistency["groups"]

            affected_values = [
                value
                for group in groups
                for value in group
            ]

            group_text = "; ".join(
                [
                    ", ".join(group)
                    for group in groups
                ]
            )

            recommendations.append(
                CleaningRecommendation(
                    issue_type="inconsistent_categories",
                    operation="standardization",
                    columns=[column],
                    affected_values=affected_values,
                    detection_method=(
                        "Case and whitespace normalization comparison"
                    ),
                    evidence=(
                        f"Column '{column}' contains categorical "
                        f"values that appear equivalent after "
                        f"normalization. Detected groups: "
                        f"{group_text}."
                    ),
                    interpretation=(
                        "Some categorical values appear to represent "
                        "the same category with differences such as "
                        "capitalization or surrounding whitespace."
                    ),
                    recommended_action="standardize",
                    confidence="high",
                    reason=(
                        f"Standardizing '{column}' can make equivalent "
                        "categorical values consistent."
                    ),
                )
            )

    # -------------------------------------------------
    # Potential outliers
    # -------------------------------------------------

    potential_outliers = ai_input[
        "quality_issues"
    ]["potential_outliers"]

    for column, outlier_info in (
        potential_outliers.items()
    ):

        outlier_count = outlier_info["count"]
        outlier_values = outlier_info["values"]
        lower_bound = outlier_info["lower_bound"]
        upper_bound = outlier_info["upper_bound"]

        if outlier_count > 0:

            recommendations.append(
                CleaningRecommendation(
                    issue_type="potential_outlier",
                    operation="remove_outliers",
                    columns=[column],
                    affected_values=outlier_values,
                    detection_method="IQR",
                    evidence=(
                        f"Column '{column}' contains "
                        f"{outlier_count} potential outlier value(s): "
                        f"{outlier_values}. "
                        f"Calculated IQR bounds are "
                        f"{lower_bound:.2f} to {upper_bound:.2f}."
                    ),
                    interpretation=(
                        "The detected values are statistically "
                        "unusual, but statistical unusualness alone "
                        "does not establish that the values are "
                        "incorrect."
                    ),
                    recommended_action="review",
                    confidence="medium",
                    reason=(
                        f"Potential outliers in '{column}' should "
                        "be reviewed before removal because they "
                        "may represent legitimate observations."
                    ),
                )
            )

    return CleaningProposal(
        summary=(
            "Cleaning recommendations were generated from "
            "detected data-quality issues. Recommendations "
            "distinguish detected issues from proposed actions "
            "and require human review before execution."
        ),
        recommendations=recommendations,
    )