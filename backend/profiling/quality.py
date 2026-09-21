import pandas as pd


def detect_quality_issues(
    df: pd.DataFrame,
) -> dict:
    """
    Detect data-quality issues in a DataFrame.

    The detector reports evidence about detected issues.
    It does not decide whether an issue should be fixed,
    removed, or otherwise modified.
    """

    issues = {
        "missing_values": {},
        "duplicate_rows": 0,
        "potential_outliers": {},
        "inconsistent_categories": {},
    }

    # -------------------------------------------------
    # Missing values
    # -------------------------------------------------

    missing = df.isnull().sum()

    for column, count in missing.items():

        if count > 0:
            issues["missing_values"][column] = int(count)

    # -------------------------------------------------
    # Duplicate rows
    # -------------------------------------------------

    duplicate_count = int(
        df.duplicated().sum()
    )

    if duplicate_count > 0:
        issues["duplicate_rows"] = duplicate_count

    # -------------------------------------------------
    # Potential numerical outliers using IQR
    # -------------------------------------------------

    numerical_columns = df.select_dtypes(
        include=["number"]
    ).columns

    for column in numerical_columns:

        series = df[column].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (
            (df[column] < lower_bound)
            |
            (df[column] > upper_bound)
        )

        outlier_values = (
            df.loc[
                outlier_mask,
                column,
            ]
            .dropna()
            .tolist()
        )

        if outlier_values:

            issues["potential_outliers"][
                column
            ] = {
                "count": len(outlier_values),
                "values": outlier_values,
                "lower_bound": float(
                    lower_bound
                ),
                "upper_bound": float(
                    upper_bound
                ),
            }

    # -------------------------------------------------
    # Inconsistent categorical values
    # -------------------------------------------------

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns

    for column in categorical_columns:

        values = (
            df[column]
            .dropna()
            .astype(str)
        )

        normalized_values = (
            values
            .str.strip()
            .str.lower()
        )

        if (
            normalized_values.nunique()
            < values.nunique()
        ):

            groups = {}

            for original, normalized in zip(
                values,
                normalized_values,
            ):

                groups.setdefault(
                    normalized,
                    set(),
                ).add(original)

            inconsistent_groups = [
                sorted(list(group))
                for group in groups.values()
                if len(group) > 1
            ]

            issues[
                "inconsistent_categories"
            ][column] = {
                "detected": True,
                "groups": inconsistent_groups,
            }

    return issues