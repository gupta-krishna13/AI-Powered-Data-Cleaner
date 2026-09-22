import os

import pytest

from backend.ai.input_schema import build_ai_analysis_input
from backend.ai.gemini_proposal_generator import generate_gemini_proposal
from backend.ai.proposal_validator import (
    validate_proposal_operations,
    validate_proposal_columns,
    validate_proposal_compatibility,
    validate_proposal_reasons,
)
from backend.ingestion.file_loader import load_file


def test_gemini_proposal_integration():

    if os.getenv("RUN_GEMINI_TEST") != "1":
        pytest.skip(
            "Gemini integration test disabled. "
            "Set RUN_GEMINI_TEST=1 to run it."
        )

    # --------------------------------------------------
    # 1. LOAD DATASET
    # --------------------------------------------------

    df = load_file(
        "tests/fixtures/messy_data.csv"
    )

    assert len(df) == 10
    assert len(df.columns) == 5

    # --------------------------------------------------
    # 2. BUILD AI INPUT
    # --------------------------------------------------

    ai_input = build_ai_analysis_input(
        df
    )

    # --------------------------------------------------
    # 3. GENERATE GEMINI PROPOSAL
    # --------------------------------------------------

    proposal = generate_gemini_proposal(
        ai_input
    )

    assert len(
        proposal.recommendations
    ) > 0

    # --------------------------------------------------
    # 4. VALIDATE OPERATIONS
    # --------------------------------------------------

    validate_proposal_operations(
        proposal
    )

    # --------------------------------------------------
    # 5. VALIDATE COLUMNS
    # --------------------------------------------------

    validate_proposal_columns(
        df,
        proposal,
    )

    # --------------------------------------------------
    # 6. VALIDATE COMPATIBILITY
    # --------------------------------------------------

    validate_proposal_compatibility(
        df,
        proposal,
    )

    # --------------------------------------------------
    # 7. VALIDATE REASONS
    # --------------------------------------------------

    validate_proposal_reasons(
        proposal
    )