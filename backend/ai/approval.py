from pydantic import BaseModel

from backend.ai.decision import RecommendationDecision
from backend.ai.proposal import CleaningProposal
from backend.ai.proposal_converter import (
    proposal_to_cleaning_request,
)
from backend.cleaning.request import CleaningRequest


class ProposalApproval(BaseModel):
    """
    Represents the user's individual decisions
    across all recommendations in a proposal.
    """

    decisions: list[RecommendationDecision]


class ApprovalRequest(BaseModel):
    """
    Represents the dataset, proposal, and the user's
    individual recommendation decisions.
    """

    saved_filename: str

    proposal: CleaningProposal

    approval: ProposalApproval


class CleaningExecutionRequest(BaseModel):
    """
    Represents a request to execute an already approved
    cleaning proposal.
    """

    approval_token: str


def approve_proposal(
    proposal: CleaningProposal,
    approval: ProposalApproval,
) -> CleaningProposal:
    """
    Validate the user's individual decisions against
    the recommendations in the proposal.
    """

    recommendation_count = len(
        proposal.recommendations
    )

    # -------------------------------------------------
    # Validate recommendation indexes
    # -------------------------------------------------

    indexes = [
        decision.recommendation_index
        for decision in approval.decisions
    ]

    expected_indexes = set(
        range(recommendation_count)
    )

    received_indexes = set(indexes)

    if received_indexes != expected_indexes:

        raise ValueError(
            "Every recommendation must have exactly "
            "one decision."
        )

    if len(indexes) != len(received_indexes):

        raise ValueError(
            "Each recommendation can only have "
            "one decision."
        )

    # -------------------------------------------------
    # Validate decision type for each recommendation
    # -------------------------------------------------

    for decision in approval.decisions:

        recommendation = proposal.recommendations[
            decision.recommendation_index
        ]

        if (
            recommendation.recommended_action
            == "review"
        ):

            allowed_decisions = {
                "keep",
                "remove",
            }

        else:

            allowed_decisions = {
                "approve",
                "reject",
            }

        if decision.decision not in allowed_decisions:

            raise ValueError(
                f"Invalid decision '{decision.decision}' "
                f"for recommendation "
                f"{decision.recommendation_index}. "
                f"Allowed decisions: "
                f"{sorted(allowed_decisions)}"
            )

    return proposal


def approve_and_convert_proposal(
    proposal: CleaningProposal,
    approval: ProposalApproval,
) -> CleaningRequest:
    """
    Validate individual recommendation decisions
    and convert only selected recommendations into
    a deterministic CleaningRequest.
    """

    approved_proposal = approve_proposal(
        proposal=proposal,
        approval=approval,
    )

    return proposal_to_cleaning_request(
        proposal=approved_proposal,
        decisions=approval.decisions,
    )