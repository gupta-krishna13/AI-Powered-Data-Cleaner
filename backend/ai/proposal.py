from typing import Any

from pydantic import BaseModel, Field


class CleaningRecommendation(BaseModel):
    """
    Represents one cleaning recommendation generated
    from a detected data-quality issue.
    """

    issue_type: str

    operation: str

    columns: list[str] = Field(
        default_factory=list
    )

    affected_values: list[Any] = Field(
        default_factory=list
    )

    detection_method: str

    evidence: str

    interpretation: str

    recommended_action: str

    confidence: str

    reason: str


class CleaningProposal(BaseModel):
    """
    Represents the complete cleaning proposal generated
    by the AI or rule-based analysis layer.
    """

    summary: str

    recommendations: list[CleaningRecommendation] = Field(
        default_factory=list
    )