from pydantic import BaseModel, Field


class CleaningRequest(BaseModel):
    """
    Defines the cleaning operations requested by the user.
    """

    median_columns: list[str] = Field(default_factory=list)
    mode_columns: list[str] = Field(default_factory=list)
    standardize_columns: list[str] = Field(default_factory=list)
    outlier_columns: list[str] = Field(default_factory=list)

    remove_duplicate_rows: bool = False
    remove_outliers: bool = False