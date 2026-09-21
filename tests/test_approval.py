from backend.ai.approval import (
    ProposalApproval,
    approve_proposal,
)
from backend.ai.decision import RecommendationDecision
from backend.ai.proposal import (
    CleaningProposal,
    CleaningRecommendation,
)


def create_test_proposal():
    return CleaningProposal(
        summary="Test cleaning proposal.",
        recommendations=[
            CleaningRecommendation(
                issue_type="missing_values",
                operation="median_imputation",
                columns=["age"],
                affected_values=[],
                detection_method="missing value count",
                evidence="The age column contains missing values.",
                interpretation="The missing numeric value can be imputed.",
                recommended_action="impute",
                confidence="high",
                reason="Median imputation is robust for numerical data.",
            )
        ],
    )


def test_approval_model():

    approval = ProposalApproval(
        decisions=[
            RecommendationDecision(
                recommendation_index=0,
                decision="approve",
            )
        ]
    )

    assert len(approval.decisions) == 1
    assert approval.decisions[0].recommendation_index == 0
    assert approval.decisions[0].decision == "approve"

    print("APPROVAL MODEL TEST: PASS")


def test_approved_proposal():

    proposal = create_test_proposal()

    approval = ProposalApproval(
        decisions=[
            RecommendationDecision(
                recommendation_index=0,
                decision="approve",
            )
        ]
    )

    result = approve_proposal(
        proposal=proposal,
        approval=approval,
    )

    assert result is proposal

    print("APPROVED PROPOSAL TEST: PASS")


def test_rejected_recommendation():

    proposal = create_test_proposal()

    approval = ProposalApproval(
        decisions=[
            RecommendationDecision(
                recommendation_index=0,
                decision="reject",
            )
        ]
    )

    result = approve_proposal(
        proposal=proposal,
        approval=approval,
    )

    assert result is proposal

    print("REJECTED RECOMMENDATION TEST: PASS")


def test_missing_decision_is_blocked():

    proposal = create_test_proposal()

    approval = ProposalApproval(
        decisions=[]
    )

    try:

        approve_proposal(
            proposal=proposal,
            approval=approval,
        )

    except ValueError as exc:

        assert str(exc) == (
            "Every recommendation must have exactly "
            "one decision."
        )

        print("MISSING DECISION TEST: PASS")
        return

    raise AssertionError(
        "Approval without a decision was not blocked."
    )


if __name__ == "__main__":

    test_approval_model()
    test_approved_proposal()
    test_rejected_recommendation()
    test_missing_decision_is_blocked()