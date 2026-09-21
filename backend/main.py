from pathlib import Path
from uuid import uuid4
from typing import Optional

import pandas as pd

from backend.ai.input_schema import (
    build_ai_analysis_input,
    validate_ai_analysis_input,
)

from backend.ai.gemini_proposal_generator import (
    generate_gemini_proposal,
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
    ApprovalRequest,
    CleaningExecutionRequest,
    approve_and_convert_proposal,
)

from backend.cleaning.pipeline import clean_dataset
from backend.cleaning.report import generate_cleaning_report
from backend.cleaning.request import CleaningRequest
from backend.cleaning.validator import validate_cleaning_request
from backend.ingestion.file_loader import load_file
from backend.profiling.profile import profile_dataset
from backend.profiling.quality import detect_quality_issues

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from fastapi.responses import FileResponse

from backend.utils.config import (
    AI_MODE,
    APP_ENV,
)


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI()


# ---------------------------------------------------------
# Temporary in-memory storage for approved cleaning requests.
# This is intentionally non-persistent for Version 1.
# ---------------------------------------------------------

approved_cleaning_requests = {}


# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "AI Data Cleaner API is running",
        "environment": APP_ENV,
    }


# ---------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Receive a CSV or Excel file, save it,
    load it into a pandas DataFrame,
    and generate a dataset profile.
    """

    allowed_extensions = [
        ".csv",
        ".xlsx",
        ".xls",
    ]

    file_extension = Path(
        file.filename
    ).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported formats: CSV and Excel."
            ),
        )

    upload_directory = Path("data/raw")
    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = (
        f"{uuid4().hex}{file_extension}"
    )

    file_path = (
        upload_directory / safe_filename
    )

    file_content = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    try:
        df = load_file(
            str(file_path)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load file: {str(exc)}",
        )

    profile = profile_dataset(df)

    quality_issues = detect_quality_issues(df)

    return {
        "message": (
            "File uploaded, profiled, and "
            "quality checked successfully"
        ),
        "filename": file.filename,
        "saved_filename": safe_filename,
        "profile": profile,
        "quality_issues": quality_issues,
    }


# ---------------------------------------------------------
# Analyze endpoint
# ---------------------------------------------------------

@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
):
    """
    Upload a CSV or Excel file, analyze its quality,
    generate a cleaning proposal, and provide a small
    dataset preview.

    This endpoint does not modify the dataset.
    """

    allowed_extensions = [
        ".csv",
        ".xlsx",
        ".xls",
    ]

    file_extension = Path(
        file.filename
    ).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported formats: CSV and Excel."
            ),
        )

    upload_directory = Path("data/raw")

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = (
        f"{uuid4().hex}{file_extension}"
    )

    file_path = (
        upload_directory / safe_filename
    )

    file_content = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # -----------------------------------------------------
    # Load dataset
    # -----------------------------------------------------

    try:
        df = load_file(
            str(file_path)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load file: {str(exc)}",
        )

    # -----------------------------------------------------
    # Build AI analysis input
    # -----------------------------------------------------

    try:
        ai_input = build_ai_analysis_input(
            df
        )

        validate_ai_analysis_input(
            ai_input
        )

        # -------------------------------------------------
        # Generate proposal
        #
        # demo  -> rule-based generator
        # gemini -> Gemini generator
        # -------------------------------------------------

        if AI_MODE == "demo":

            proposal = generate_rule_based_proposal(
                ai_input
            )

        else:

            proposal = generate_gemini_proposal(
                ai_input
            )

        # -------------------------------------------------
        # Validate generated proposal
        # -------------------------------------------------

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

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # -----------------------------------------------------
    # Dataset preview
    # -----------------------------------------------------

    preview_df = df.head(5).copy()

    # Convert missing values to None so they become
    # proper JSON null values in the API response.
    preview_df = preview_df.astype(
        object
    ).where(
        pd.notna(preview_df),
        None,
    )

    preview = preview_df.to_dict(
        orient="records"
    )

    # -----------------------------------------------------
    # Return analysis response
    # -----------------------------------------------------

    return {
        "message": "File analyzed successfully",
        "filename": file.filename,
        "saved_filename": safe_filename,
        "profile": ai_input["profile"],
        "quality_issues": ai_input[
            "quality_issues"
        ],
        "proposal": proposal.model_dump(),
        "preview": preview,
    }


# ---------------------------------------------------------
# Approve endpoint
# ---------------------------------------------------------

@app.post("/approve")
async def approve_cleaning_proposal(
    request: ApprovalRequest,
):
    """
    Process the user's individual decisions for a cleaning proposal.

    The proposal is validated against the dataset
    identified by saved_filename.

    Individual recommendation decisions are converted into
    a deterministic CleaningRequest and temporarily stored
    in memory.

    This endpoint does not execute cleaning.
    """

    # -----------------------------------------------------
    # Individual recommendation decisions are processed by
    # approve_and_convert_proposal() below.
    # There is intentionally no whole-proposal approved flag.
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Prevent path traversal and ensure we only access
    # files inside the raw data directory.
    # -----------------------------------------------------

    safe_filename = Path(
        request.saved_filename
    ).name

    if safe_filename != request.saved_filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid saved filename.",
        )

    file_path = (
        Path("data/raw") / safe_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Original dataset not found.",
        )

    # -----------------------------------------------------
    # Validate proposal
    # -----------------------------------------------------

    try:
        df = load_file(
            str(file_path)
        )

        validate_proposal_operations(
            request.proposal
        )

        validate_proposal_columns(
            df,
            request.proposal,
        )

        validate_proposal_compatibility(
            df,
            request.proposal,
        )

        validate_proposal_reasons(
            request.proposal
        )

        cleaning_request = (
            approve_and_convert_proposal(
                proposal=request.proposal,
                approval=request.approval,
            )
        )

        validate_cleaning_request(
            df=df,
            request=cleaning_request,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # -----------------------------------------------------
    # Create approval token
    # -----------------------------------------------------

    approval_token = uuid4().hex

    approved_cleaning_requests[
        approval_token
    ] = {
        "saved_filename": safe_filename,
        "cleaning_request": cleaning_request,
    }

    return {
        "message": (
            "Cleaning proposal approved successfully"
        ),
        "approval_token": approval_token,
        "saved_filename": safe_filename,
        "cleaning_request": (
            cleaning_request.model_dump()
        ),
    }


# ---------------------------------------------------------
# Execute approved cleaning endpoint
# ---------------------------------------------------------

@app.post("/execute-cleaning")
async def execute_approved_cleaning(
    request: CleaningExecutionRequest,
):
    """
    Execute a previously approved cleaning proposal.

    This endpoint retrieves the approved CleaningRequest
    from temporary in-memory storage and passes it to
    the deterministic cleaning engine.
    """

    approval_data = (
        approved_cleaning_requests.get(
            request.approval_token
        )
    )

    if approval_data is None:
        raise HTTPException(
            status_code=404,
            detail="Approval token not found or expired.",
        )

    safe_filename = approval_data[
        "saved_filename"
    ]

    cleaning_request = approval_data[
        "cleaning_request"
    ]

    file_path = (
        Path("data/raw") / safe_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Original dataset not found.",
        )

    # -----------------------------------------------------
    # Execute deterministic cleaning
    # -----------------------------------------------------

    try:
        df = load_file(
            str(file_path)
        )

        validate_cleaning_request(
            df=df,
            request=cleaning_request,
        )

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

        report = generate_cleaning_report(
            original_df=df,
            cleaned_df=cleaned_df,
            audit=audit,
        )

        processed_directory = Path(
            "data/processed"
        )

        processed_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        cleaned_filename = (
            f"cleaned_{uuid4().hex}.csv"
        )

        cleaned_file_path = (
            processed_directory /
            cleaned_filename
        )

        cleaned_df.to_csv(
            cleaned_file_path,
            index=False,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # -----------------------------------------------------
    # Consume the approval token after successful execution.
    # -----------------------------------------------------

    del approved_cleaning_requests[
        request.approval_token
    ]

    return {
        "message": (
            "Approved cleaning executed successfully"
        ),
        "original_filename": safe_filename,
        "cleaned_filename": cleaned_filename,
        "audit": audit,
        "report": report,
    }


# ---------------------------------------------------------
# Cleaning request helper
# ---------------------------------------------------------

def get_cleaning_request(
    median_columns: Optional[str] = Form(None),
    mode_columns: Optional[str] = Form(None),
    standardize_columns: Optional[str] = Form(None),
    outlier_columns: Optional[str] = Form(None),
    remove_duplicate_rows: bool = Form(False),
    remove_outliers: bool = Form(False),
) -> CleaningRequest:
    """
    Convert multipart form fields into a
    CleaningRequest model.
    """

    return CleaningRequest(
        median_columns=[
            column.strip()
            for column in median_columns.split(",")
            if column.strip()
        ] if median_columns else [],

        mode_columns=[
            column.strip()
            for column in mode_columns.split(",")
            if column.strip()
        ] if mode_columns else [],

        standardize_columns=[
            column.strip()
            for column in standardize_columns.split(",")
            if column.strip()
        ] if standardize_columns else [],

        outlier_columns=[
            column.strip()
            for column in outlier_columns.split(",")
            if column.strip()
        ] if outlier_columns else [],

        remove_duplicate_rows=(
            remove_duplicate_rows
        ),

        remove_outliers=(
            remove_outliers
        ),
    )


# ---------------------------------------------------------
# Direct cleaning endpoint
# ---------------------------------------------------------

@app.post("/clean")
async def clean_file(
    file: UploadFile = File(...),
    cleaning_request: CleaningRequest = Depends(
        get_cleaning_request
    ),
):
    """
    Upload a CSV or Excel file and apply selected
    deterministic cleaning operations.
    """

    allowed_extensions = [
        ".csv",
        ".xlsx",
        ".xls",
    ]

    file_extension = Path(
        file.filename
    ).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported formats: CSV and Excel."
            ),
        )

    upload_directory = Path(
        "data/raw"
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = (
        f"{uuid4().hex}{file_extension}"
    )

    file_path = (
        upload_directory / safe_filename
    )

    file_content = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    try:
        df = load_file(
            str(file_path)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load file: {str(exc)}",
        )

    # -----------------------------------------------------
    # Validate and clean
    # -----------------------------------------------------

    try:
        validate_cleaning_request(
            df=df,
            request=cleaning_request,
        )

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

        report = generate_cleaning_report(
            original_df=df,
            cleaned_df=cleaned_df,
            audit=audit,
        )

        processed_directory = Path(
            "data/processed"
        )

        processed_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        cleaned_filename = (
            f"cleaned_{uuid4().hex}.csv"
        )

        cleaned_file_path = (
            processed_directory /
            cleaned_filename
        )

        cleaned_df.to_csv(
            cleaned_file_path,
            index=False,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "File cleaned successfully",
        "filename": file.filename,
        "saved_filename": safe_filename,
        "cleaned_filename": cleaned_filename,
        "audit": audit,
        "report": report,
    }


# ---------------------------------------------------------
# Download endpoint
# ---------------------------------------------------------

@app.get("/download/{filename}")
async def download_cleaned_file(
    filename: str,
):
    """
    Download a cleaned dataset from the
    processed directory.
    """

    processed_directory = Path(
        "data/processed"
    ).resolve()

    safe_filename = Path(filename).name

    if safe_filename != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    file_path = (
        processed_directory / safe_filename
    ).resolve()

    if processed_directory not in file_path.parents:
        raise HTTPException(
            status_code=400,
            detail="Invalid file path.",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Cleaned file not found.",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="Requested path is not a file.",
        )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/csv",
    )