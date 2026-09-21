from typing import Literal

from pydantic import BaseModel


class RecommendationDecision(BaseModel):
    """
    Represents the user's decision for one
    individual cleaning recommendation.
    """

    recommendation_index: int

    decision: Literal[
        "approve",
        "reject",
        "keep",
        "remove",
    ]