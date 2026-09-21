import pandas as pd


def standardize_categories(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Standardize categorical values by removing extra spaces
    and normalizing capitalization.
    """

    cleaned_df = df.copy()

    for column in columns:
        if column not in cleaned_df.columns:
            raise ValueError(f"Column not found: {column}")

        if not pd.api.types.is_object_dtype(cleaned_df[column]):
            raise TypeError(
                f"Column '{column}' must contain categorical/text data."
            )

        cleaned_df[column] = (
            cleaned_df[column]
            .str.strip()
            .str.title()
        )

    return cleaned_df