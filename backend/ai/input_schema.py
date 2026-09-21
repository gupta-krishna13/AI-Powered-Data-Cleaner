import pandas as pd


def build_column_metadata(df: pd.DataFrame) -> dict:
    """
    Build structured metadata for every column
    in the dataset.
    """

    metadata = {}

    for column in df.columns:
        series = df[column]

        metadata[column] = {
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": float(
                series.isna().mean() * 100
            ),
            "unique_values": int(
                series.nunique(dropna=True)
            ),
        }

    return metadata

def build_ai_analysis_input(df: pd.DataFrame) -> dict:
    """
    Build the structured input that will be provided
    to the AI analysis layer.
    """

    from backend.profiling.profile import profile_dataset
    from backend.profiling.quality import detect_quality_issues

    profile = profile_dataset(df)
    quality_issues = detect_quality_issues(df)
    column_metadata = build_column_metadata(df)

    return {
        "dataset": {
            "rows": profile["rows"],
            "columns": profile["columns"],
        },
        "profile": profile,
        "quality_issues": quality_issues,
        "column_metadata": column_metadata,
    }
    
def validate_ai_analysis_input(ai_input: dict) -> None:
    """
    Validate the structure of the AI analysis input.
    """

    required_sections = [
        "dataset",
        "profile",
        "quality_issues",
        "column_metadata",
    ]

    missing_sections = [
        section
        for section in required_sections
        if section not in ai_input
    ]

    if missing_sections:
        raise ValueError(
            f"Missing AI input sections: {missing_sections}"
        )

    if "rows" not in ai_input["dataset"]:
        raise ValueError(
            "AI input dataset section is missing 'rows'."
        )

    if "columns" not in ai_input["dataset"]:
        raise ValueError(
            "AI input dataset section is missing 'columns'."
        )