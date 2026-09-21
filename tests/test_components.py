from pathlib import Path

from backend.ingestion.file_loader import load_file
from backend.profiling.profile import profile_dataset
from backend.profiling.quality import detect_quality_issues

from backend.ai.input_schema import (
    build_column_metadata,
    build_ai_analysis_input,
    validate_ai_analysis_input,
)

from backend.ai.proposal_generator import (
    generate_rule_based_proposal,
)

from backend.ai.proposal_validator import (
    validate_proposal_operations,
    validate_proposal_columns,
    validate_proposal_compatibility,
    validate_proposal_reasons,
)

from backend.ai.decision import (
    RecommendationDecision,
)

from backend.ai.proposal_converter import (
    proposal_to_cleaning_request,
)

from backend.cleaning.validator import (
    validate_cleaning_request,
)

from backend.cleaning.pipeline import (
    clean_dataset,
)

from backend.cleaning.report import (
    generate_cleaning_report,
)


DATASET_PATH = Path(
    "data/raw/messy_data.csv"
)


def test_all_components():

    print("\n==============================")
    print("AI DATA CLEANER COMPONENT TEST")
    print("==============================\n")

    # --------------------------------------------------
    # 1. INGESTION
    # --------------------------------------------------

    print("[1] Testing ingestion...")

    df = load_file(
        str(DATASET_PATH)
    )

    assert len(df) == 10
    assert len(df.columns) == 5

    print("    PASS - CSV ingestion")


    # --------------------------------------------------
    # 2. PROFILING
    # --------------------------------------------------

    print("\n[2] Testing profiling...")

    profile = profile_dataset(df)

    assert profile["rows"] == 10
    assert profile["columns"] == 5
    assert profile["duplicate_rows"] == 1

    assert (
        profile["missing_values"]["age"]
        == 2
    )

    assert (
        profile["missing_values"]["city"]
        == 1
    )

    assert (
        profile["missing_values"]["salary"]
        == 1
    )

    print("    PASS - Dataset profiling")


    # --------------------------------------------------
    # 3. QUALITY DETECTION
    # --------------------------------------------------

    print("\n[3] Testing quality detection...")

    quality = detect_quality_issues(df)

    # Missing values

    assert (
        quality["missing_values"]["age"]
        == 2
    )

    assert (
        quality["missing_values"]["city"]
        == 1
    )

    assert (
        quality["missing_values"]["salary"]
        == 1
    )

    # Duplicate rows

    assert (
        quality["duplicate_rows"]
        == 1
    )

    # Potential outlier evidence

    assert (
        quality["potential_outliers"]["age"]["count"]
        == 1
    )

    assert (
        200
        in quality["potential_outliers"]["age"]["values"]
    )

    # Inconsistent category evidence

    assert (
        quality[
            "inconsistent_categories"
        ]["city"]["detected"]
        is True
    )

    city_groups = quality[
        "inconsistent_categories"
    ]["city"]["groups"]

    assert (
        ["Delhi", "delhi"]
        in city_groups
    )

    print("    PASS - Quality detection")


    # --------------------------------------------------
    # 4. AI INPUT
    # --------------------------------------------------

    print("\n[4] Testing AI input schema...")

    metadata = build_column_metadata(df)

    assert "age" in metadata

    assert (
        metadata["age"]["missing_count"]
        == 2
    )

    ai_input = build_ai_analysis_input(df)

    validate_ai_analysis_input(
        ai_input
    )

    assert "dataset" in ai_input
    assert "profile" in ai_input
    assert "quality_issues" in ai_input
    assert "column_metadata" in ai_input

    print("    PASS - AI input schema")


    # --------------------------------------------------
    # 5. AI PROPOSAL GENERATOR
    # --------------------------------------------------

    print("\n[5] Testing AI proposal generator...")

    proposal = generate_rule_based_proposal(
        ai_input
    )

    assert (
        len(proposal.recommendations)
        == 6
    )

    operations = [
        recommendation.operation
        for recommendation
        in proposal.recommendations
    ]

    assert (
        "median_imputation"
        in operations
    )

    assert (
        "mode_imputation"
        in operations
    )

    assert (
        "standardization"
        in operations
    )

    assert (
        "remove_duplicates"
        in operations
    )

    assert (
        "remove_outliers"
        in operations
    )

    print("    PASS - Proposal generation")


    # --------------------------------------------------
    # 6. PROPOSAL VALIDATION
    # --------------------------------------------------

    print("\n[6] Testing proposal validation...")

    validate_proposal_operations(
        proposal
    )

    validate_proposal_columns(
        df,
        proposal,
    )

    validate_proposal_compatibility(
        df,
        proposal,
    )

    validate_proposal_reasons(
        proposal
    )

    print("    PASS - Proposal validation")


    # --------------------------------------------------
    # 7. PROPOSAL CONVERSION
    # --------------------------------------------------

    print("\n[7] Testing proposal conversion...")

    # Simulate human decisions.
    #
    # Normal recommendations:
    #     approve
    #
    # Review recommendations:
    #     keep
    #
    # This means the user accepts the safe
    # cleaning operations but does NOT approve
    # destructive review-type operations.

    decisions = []

    for index, recommendation in enumerate(
        proposal.recommendations
    ):

        if (
            recommendation.recommended_action
            == "review"
        ):

            decisions.append(
                RecommendationDecision(
                    recommendation_index=index,
                    decision="keep",
                )
            )

        else:

            decisions.append(
                RecommendationDecision(
                    recommendation_index=index,
                    decision="approve",
                )
            )

    cleaning_request = (
        proposal_to_cleaning_request(
            proposal=proposal,
            decisions=decisions,
        )
    )

    # --------------------------------------------------
    # Verify approved operations
    # --------------------------------------------------

    assert (
        "age"
        in cleaning_request.median_columns
    )

    assert (
        "salary"
        in cleaning_request.median_columns
    )

    assert (
        "city"
        in cleaning_request.mode_columns
    )

    assert (
        "city"
        in cleaning_request.standardize_columns
    )

    # --------------------------------------------------
    # Verify review-type operations were kept
    # --------------------------------------------------

    # The outlier recommendation was marked "keep",
    # so it must NOT become an executable operation.

    assert (
        "age"
        not in cleaning_request.outlier_columns
    )

    assert (
        cleaning_request.remove_outliers
        is False
    )

    # The duplicate recommendation was also marked "keep",
    # so duplicate removal must not be executed.

    assert (
        cleaning_request.remove_duplicate_rows
        is False
    )

    print(
        "    PASS - Proposal conversion"
    )

    # --------------------------------------------------
    # 8. CLEANING REQUEST VALIDATION
    # --------------------------------------------------

    print(
        "\n[8] Testing cleaning request validation..."
    )

    validate_cleaning_request(
        df=df,
        request=cleaning_request,
    )

    print(
        "    PASS - Cleaning request validation"
    )


    # --------------------------------------------------
    # 9. CLEANING PIPELINE
    # --------------------------------------------------

    print("\n[9] Testing cleaning pipeline...")

    cleaned_df, audit = clean_dataset(
        df=df,
        median_columns=(
            cleaning_request.median_columns
        ),
        mode_columns=(
            cleaning_request.mode_columns
        ),
        standardize_columns=(
            cleaning_request.standardize_columns
        ),
        outlier_columns=(
            cleaning_request.outlier_columns
        ),
        remove_duplicate_rows=(
            cleaning_request.remove_duplicate_rows
        ),
        remove_outliers=(
            cleaning_request.remove_outliers
        ),
    )

    # --------------------------------------------------
    # Verify missing values were cleaned
    # --------------------------------------------------

    assert (
        cleaned_df["age"].isna().sum()
        == 0
    )

    assert (
        cleaned_df["salary"].isna().sum()
        == 0
    )

    assert (
        cleaned_df["city"].isna().sum()
        == 0
    )

    # --------------------------------------------------
    # Verify standardization
    # --------------------------------------------------

    assert (
        cleaned_df["city"]
        .str.contains("Delhi")
        .any()
    )

    # --------------------------------------------------
    # Verify review decisions were respected
    # --------------------------------------------------

    # The duplicate should still exist because
    # the user chose "keep".

    assert (
        len(cleaned_df)
        == 10
    )

    # The outlier value 200 should still exist
    # because the user chose "keep".

    assert (
        200
        in cleaned_df["age"].values
    )

    print(
        "    PASS - Cleaning pipeline"
    )


    # --------------------------------------------------
    # 10. CLEANING REPORT
    # --------------------------------------------------

    print("\n[10] Testing cleaning report...")

    report = generate_cleaning_report(
        original_df=df,
        cleaned_df=cleaned_df,
        audit=audit,
    )

    assert (
        report["rows_before"]
        == 10
    )

    # No rows should be removed because
    # duplicate and outlier removal were
    # not approved.

    assert (
        report["rows_after"]
        == 10
    )

    assert (
        report["rows_removed"]
        == 0
    )

    assert (
        "missing_values"
        in report
    )

    assert (
        "duplicates_removed"
        in report
    )

    assert (
        "outliers_removed"
        in report
    )

    assert (
        report["duplicates_removed"]
        == 0
    )

    assert (
        report["outliers_removed"]
        == 0
    )

    print(
        "    PASS - Cleaning report"
    )


    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n==============================")
    print("ALL COMPONENT TESTS PASSED")
    print("==============================\n")


if __name__ == "__main__":
    test_all_components()