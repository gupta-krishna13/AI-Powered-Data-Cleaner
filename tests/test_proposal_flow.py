from pathlib import Path

from backend.ingestion.file_loader import load_file

from backend.ai.input_schema import (
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

from backend.ai.approval import (
    ProposalApproval,
    approve_and_convert_proposal,
)

from backend.ai.decision import (
    RecommendationDecision,
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
    "tests/fixtures/messy_data.csv"
)


def test_approved_proposal_flow():

    print("\n==============================")
    print("APPROVED PROPOSAL FLOW TEST")
    print("==============================\n")

    # --------------------------------------------------
    # 1. LOAD DATASET
    # --------------------------------------------------

    df = load_file(
        str(DATASET_PATH)
    )

    print("[1] Dataset loaded")


    # --------------------------------------------------
    # 2. BUILD AI INPUT
    # --------------------------------------------------

    ai_input = build_ai_analysis_input(
        df
    )

    validate_ai_analysis_input(
        ai_input
    )

    print("[2] AI input validated")


    # --------------------------------------------------
    # 3. GENERATE PROPOSAL
    # --------------------------------------------------

    proposal = generate_rule_based_proposal(
        ai_input
    )

    print(
        f"[3] Proposal generated with "
        f"{len(proposal.recommendations)} recommendations"
    )


    # --------------------------------------------------
    # 4. VALIDATE PROPOSAL
    # --------------------------------------------------

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

    print("[4] Proposal validated")


    # --------------------------------------------------
    # 5. USER DECISIONS
    # --------------------------------------------------

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
                    decision="remove",
                )
            )

        else:

            decisions.append(
                RecommendationDecision(
                    recommendation_index=index,
                    decision="approve",
                )
            )

    approval = ProposalApproval(
        decisions=decisions
    )

    print(
        f"[5] {len(decisions)} individual "
        "recommendation decisions created"
    )


    # --------------------------------------------------
    # 6. APPROVE AND CONVERT
    # --------------------------------------------------

    cleaning_request = (
        approve_and_convert_proposal(
            proposal=proposal,
            approval=approval,
        )
    )

    print(
        "[6] Proposal approved and converted"
    )


    # --------------------------------------------------
    # 7. VERIFY CLEANING REQUEST
    # --------------------------------------------------

    assert "age" in cleaning_request.median_columns
    assert "salary" in cleaning_request.median_columns

    assert "city" in cleaning_request.mode_columns

    assert "city" in cleaning_request.standardize_columns

    assert "age" in cleaning_request.outlier_columns

    assert (
        cleaning_request.remove_outliers
        is True
    )

    assert (
        cleaning_request.remove_duplicate_rows
        is True
    )

    print(
        "[7] Cleaning request contains "
        "all approved operations"
    )


    # --------------------------------------------------
    # 8. VALIDATE CLEANING REQUEST
    # --------------------------------------------------

    validate_cleaning_request(
        df=df,
        request=cleaning_request,
    )

    print(
        "[8] Cleaning request validated"
    )


    # --------------------------------------------------
    # 9. EXECUTE CLEANING
    # --------------------------------------------------

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

    print(
        "[9] Cleaning executed"
    )


    # --------------------------------------------------
    # 10. GENERATE REPORT
    # --------------------------------------------------

    report = generate_cleaning_report(
        original_df=df,
        cleaned_df=cleaned_df,
        audit=audit,
    )

    print(
        "[10] Cleaning report generated"
    )


    # --------------------------------------------------
    # 11. FINAL ASSERTIONS
    # --------------------------------------------------

    assert report["rows_before"] == 10
    assert report["rows_after"] == 8

    assert audit["duplicates_removed"] == 1
    assert audit["outliers_removed"] == 1

    assert (
        audit["missing_values"]["age"]["filled"]
        == 2
    )

    assert (
        audit["missing_values"]["salary"]["filled"]
        == 1
    )

    assert (
        audit["missing_values"]["city"]["filled"]
        == 1
    )

    assert (
        "city"
        in audit["standardized_columns"]
    )

    print(
        "[11] Final assertions passed"
    )

    print("\n==============================")
    print("APPROVED PROPOSAL FLOW: PASS")
    print("==============================\n")


if __name__ == "__main__":
    test_approved_proposal_flow()