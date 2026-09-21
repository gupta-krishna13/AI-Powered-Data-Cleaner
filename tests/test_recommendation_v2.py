from pathlib import Path

from backend.ingestion.file_loader import load_file
from backend.ai.input_schema import (
    build_ai_analysis_input,
)
from backend.ai.proposal_generator import (
    generate_rule_based_proposal,
)


DATASET_PATH = Path(
    "data/raw/messy_test_dataset_2.csv"
)


def test_recommendation_engine_v2():

    print("\n==============================")
    print("RECOMMENDATION ENGINE V2 TEST")
    print("==============================\n")

    # --------------------------------------------------
    # 1. LOAD DATASET
    # --------------------------------------------------

    print("[1] Loading test dataset...")

    df = load_file(
        str(DATASET_PATH)
    )

    assert len(df) == 15
    assert len(df.columns) == 8

    print("    PASS - Dataset loaded")


    # --------------------------------------------------
    # 2. BUILD AI INPUT
    # --------------------------------------------------

    print("\n[2] Building AI analysis input...")

    ai_input = build_ai_analysis_input(
        df
    )

    print("    PASS - AI input built")


    # --------------------------------------------------
    # 3. GENERATE PROPOSAL
    # --------------------------------------------------

    print("\n[3] Generating Recommendation Engine v2 proposal...")

    proposal = generate_rule_based_proposal(
        ai_input
    )

    assert len(proposal.recommendations) > 0

    print(
        f"    PASS - "
        f"{len(proposal.recommendations)} recommendations generated"
    )


    # --------------------------------------------------
    # 4. CHECK NEW FIELDS
    # --------------------------------------------------

    print("\n[4] Checking new recommendation fields...")

    required_fields = [
        "issue_type",
        "operation",
        "columns",
        "affected_values",
        "detection_method",
        "evidence",
        "interpretation",
        "recommended_action",
        "confidence",
        "reason",
    ]

    for recommendation in proposal.recommendations:

        for field in required_fields:

            assert hasattr(
                recommendation,
                field,
            )

    print(
        "    PASS - All Recommendation Engine v2 fields present"
    )


    # --------------------------------------------------
    # 5. CHECK OUTLIER RECOMMENDATIONS
    # --------------------------------------------------

    print("\n[5] Checking outlier recommendations...")

    outlier_recommendations = [
        recommendation
        for recommendation in proposal.recommendations
        if recommendation.issue_type
        == "potential_outlier"
    ]

    assert len(outlier_recommendations) > 0

    for recommendation in outlier_recommendations:

        assert (
            recommendation.operation
            == "remove_outliers"
        )

        assert (
            recommendation.recommended_action
            == "review"
        )

        assert (
            recommendation.confidence
            == "medium"
        )

        assert (
            recommendation.detection_method
            == "IQR"
        )

        assert (
            recommendation.interpretation.strip()
        )

        assert (
            recommendation.reason.strip()
        )

    print(
        "    PASS - Outliers are recommended for REVIEW"
    )


    # --------------------------------------------------
    # 6. CHECK DUPLICATE RECOMMENDATIONS
    # --------------------------------------------------

    print("\n[6] Checking duplicate recommendations...")

    duplicate_recommendations = [
        recommendation
        for recommendation in proposal.recommendations
        if recommendation.issue_type
        == "duplicate_rows"
    ]

    assert len(duplicate_recommendations) == 1

    duplicate = duplicate_recommendations[0]

    assert (
        duplicate.operation
        == "remove_duplicates"
    )

    assert (
        duplicate.recommended_action
        == "review"
    )

    assert (
        duplicate.confidence
        == "high"
    )

    print(
        "    PASS - Duplicate rows require review"
    )


    # --------------------------------------------------
    # 7. CHECK STANDARDIZATION
    # --------------------------------------------------

    print("\n[7] Checking standardization recommendations...")

    standardization_recommendations = [
        recommendation
        for recommendation in proposal.recommendations
        if recommendation.issue_type
        == "inconsistent_categories"
    ]

    assert len(
        standardization_recommendations
    ) > 0

    for recommendation in (
        standardization_recommendations
    ):

        assert (
            recommendation.operation
            == "standardization"
        )

        assert (
            recommendation.recommended_action
            == "standardize"
        )

        assert (
            recommendation.confidence
            == "high"
        )

    print(
        "    PASS - Category inconsistencies "
        "recommend standardization"
    )


    # --------------------------------------------------
    # 8. CHECK MISSING VALUE RECOMMENDATIONS
    # --------------------------------------------------

    print("\n[8] Checking missing-value recommendations...")

    missing_recommendations = [
        recommendation
        for recommendation in proposal.recommendations
        if recommendation.issue_type
        == "missing_values"
    ]

    assert len(
        missing_recommendations
    ) > 0

    operations = [
        recommendation.operation
        for recommendation in missing_recommendations
    ]

    assert (
        "median_imputation"
        in operations
    )

    assert (
        "mode_imputation"
        in operations
    )

    for recommendation in (
        missing_recommendations
    ):

        assert (
            recommendation.recommended_action
            == "impute"
        )

    print(
        "    PASS - Missing values receive "
        "explicit imputation recommendations"
    )


    # --------------------------------------------------
    # 9. PRINT PROPOSAL SUMMARY
    # --------------------------------------------------

    print("\n[9] Recommendation summary...")

    for index, recommendation in enumerate(
        proposal.recommendations,
        start=1,
    ):

        print(
            f"\n    Recommendation {index}"
        )

        print(
            f"    Issue type: "
            f"{recommendation.issue_type}"
        )

        print(
            f"    Operation: "
            f"{recommendation.operation}"
        )

        print(
            f"    Action: "
            f"{recommendation.recommended_action}"
        )

        print(
            f"    Confidence: "
            f"{recommendation.confidence}"
        )

        print(
            f"    Detection: "
            f"{recommendation.detection_method}"
        )


    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n==============================")
    print("RECOMMENDATION ENGINE V2 PASSED")
    print("==============================\n")


if __name__ == "__main__":
    test_recommendation_engine_v2()