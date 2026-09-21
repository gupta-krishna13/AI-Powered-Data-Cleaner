import json
import time

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from backend.ai.proposal import CleaningProposal
from backend.utils.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_FALLBACK_MODEL,
)


# ---------------------------------------------------------
# Gemini retry configuration
# ---------------------------------------------------------

# Give the primary model one retry for transient 5xx errors
# such as HTTP 503 Service Unavailable.
PRIMARY_MAX_ATTEMPTS = 2

# The fallback is intended to be a fast safety net.
FALLBACK_MAX_ATTEMPTS = 1

INITIAL_RETRY_DELAY = 2


def _generate_with_model(
    client,
    model: str,
    prompt: str,
    max_attempts: int,
) -> CleaningProposal:
    """
    Generate a cleaning proposal using one Gemini model.

    ServerError responses may be retried according to
    max_attempts.

    ClientError 429 responses are not retried here because
    they indicate quota/rate-limit exhaustion. The caller
    can decide whether to switch to a fallback model.

    Other ClientError responses are raised immediately.

    Gemini 3.8 Flash uses low thinking to reduce latency.
    The fallback model does not receive a thinking override.
    """

    for attempt in range(1, max_attempts + 1):

        try:
            print(
                f"Trying Gemini model '{model}' "
                f"(attempt {attempt}/{max_attempts})..."
            )

            config_kwargs = {
                "response_mime_type": "application/json",
                "automatic_function_calling": (
                    types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                ),
            }

            # Gemini 3.8 Flash supports low/medium/high
            # thinking. Low is appropriate for this fast
            # data-quality analysis workflow.
            if model == GEMINI_MODEL:
                config_kwargs["thinking_config"] = (
                    types.ThinkingConfig(
                        thinking_level="low"
                    )
                )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    **config_kwargs
                ),
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            try:
                response_data = json.loads(
                    response.text
                )

            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Gemini returned invalid JSON: {str(exc)}"
                ) from exc

            try:
                proposal = CleaningProposal.model_validate(
                    response_data
                )

            except Exception as exc:
                raise ValueError(
                    "Gemini response does not match "
                    f"CleaningProposal schema: {str(exc)}"
                ) from exc

            return proposal

        except ClientError as exc:

            if exc.code == 429:
                print(
                    f"Gemini model '{model}' returned "
                    "429 RESOURCE_EXHAUSTED."
                )

                raise

            raise

        except ServerError:

            if attempt == max_attempts:
                print(
                    f"Gemini model '{model}' failed after "
                    f"{max_attempts} attempt(s)."
                )

                raise

            delay = INITIAL_RETRY_DELAY * (
                2 ** (attempt - 1)
            )

            print(
                f"Gemini server error from '{model}'. "
                f"Retrying in {delay} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Gemini model '{model}' failed unexpectedly."
    )


def generate_gemini_proposal(
    ai_input: dict,
) -> CleaningProposal:
    """
    Generate a structured cleaning proposal using Gemini.

    Gemini only recommends cleaning operations.
    It does not execute any cleaning operation.

    Primary model:
        - Up to two attempts for transient ServerError.
        - Uses low thinking for lower latency.
        - 429 triggers fallback.

    Fallback model:
        - One attempt.
        - Intended to be a fast safety net.

    Gemini returns JSON, which is then validated
    by our own Pydantic CleaningProposal schema.
    """

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    prompt = f"""
You are an AI data-quality analyst.

Analyze ONLY the supplied dataset-quality information and generate
a conservative cleaning proposal.

Your output will be validated by a strict Pydantic schema before it
can reach the human approval stage.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. The JSON must contain exactly these top-level fields:
   - summary
   - recommendations

3. Every item in "recommendations" MUST contain ALL of these fields:
   - issue_type
   - operation
   - columns
   - affected_values
   - detection_method
   - evidence
   - interpretation
   - recommended_action
   - confidence
   - reason

4. Never omit any of the fields above.
5. Use an empty list [] when a list field has no values.
6. Do not invent column names.
7. Do not invent quality issues that are not present in the supplied
   quality information.
8. Do not execute cleaning.
9. Do not write Python code.
10. Do not write SQL.
11. Every recommendation must have a meaningful reason.
12. Consider every detected actionable quality issue.
13. Do not merge unrelated issues into one recommendation.
14. Prefer one recommendation per detected issue/affected column so
    each recommendation can be reviewed independently by the user.
15. Keep the recommendation specific to the evidence supplied.

SUPPORTED OPERATIONS:

- median_imputation
  Use for detected missing values in numerical columns.

- mode_imputation
  Use for detected missing values in categorical/text columns.

- standardization
  Use for detected inconsistent categorical/text values.

- remove_outliers
  Use for detected potential numerical outliers.

- remove_duplicates
  Use for detected duplicate rows.

OPERATION RULES:

- median_imputation:
  columns must contain only numerical columns with detected missing
  values.

- mode_imputation:
  columns must contain only categorical/text columns with detected
  missing values.

- standardization:
  columns must contain only categorical/text columns for which
  inconsistent values were detected.

- remove_outliers:
  columns must contain only numerical columns for which potential
  outliers were detected.

- remove_duplicates:
  columns MUST be [].

RECOMMENDATION FIELD RULES:

- issue_type:
  Use one of:
  "missing_values"
  "duplicate_rows"
  "inconsistent_categories"
  "potential_outlier"

- operation:
  Must be one of the five supported operations above.

- columns:
  Use the exact dataset column names.

- affected_values:
  Include the actual detected values when they are supplied by the
  quality analysis. Otherwise use [].

- detection_method:
  Describe the method that produced the supplied evidence, such as
  "Missing-value detection", "Exact row comparison",
  "Case and whitespace normalization comparison", or "IQR".

- evidence:
  State the concrete evidence from the supplied quality analysis.
  Include counts, values, groups, or bounds when available.

- interpretation:
  Explain what the detected issue means without claiming that a
  statistically unusual value is necessarily incorrect.

- recommended_action:
  For median_imputation use "impute".
  For mode_imputation use "impute".
  For standardization use "standardize".
  For remove_outliers use "review".
  For remove_duplicates use "review".

- confidence:
  Use only "high", "medium", or "low".

- reason:
  Explain why the proposed operation is appropriate for this
  particular detected issue.

IMPORTANT:

Do not use the AI recommendation to decide whether destructive
operations should happen automatically.

For remove_outliers and remove_duplicates:
- recommend the operation,
- set recommended_action to "review",
- explain why human review is required.

The human approval layer will decide whether the operation is
actually executed.

EXPECTED JSON SHAPE:

{{
  "summary": "Short summary of the detected quality issues and proposed actions.",
  "recommendations": [
    {{
      "issue_type": "missing_values",
      "operation": "median_imputation",
      "columns": ["quantity"],
      "affected_values": [],
      "detection_method": "Missing-value detection",
      "evidence": "Column 'quantity' contains 1 missing numerical value.",
      "interpretation": "The missing numerical value may affect analysis and downstream processing.",
      "recommended_action": "impute",
      "confidence": "high",
      "reason": "Median imputation is a conservative candidate for a missing numerical value because the median is less sensitive to extreme values than the mean."
    }}
  ]
}}

DATASET ANALYSIS INPUT:

{ai_input}
"""

    # ---------------------------------------------------------
    # 1. Try the primary model
    # ---------------------------------------------------------

    try:
        return _generate_with_model(
            client=client,
            model=GEMINI_MODEL,
            prompt=prompt,
            max_attempts=PRIMARY_MAX_ATTEMPTS,
        )

    except (ServerError, ClientError) as primary_error:

        if isinstance(primary_error, ClientError):
            if primary_error.code != 429:
                raise

            print(
                f"Primary Gemini model '{GEMINI_MODEL}' "
                "quota is unavailable."
            )

        else:
            print(
                f"Primary Gemini model '{GEMINI_MODEL}' "
                "is unavailable after the configured retries."
            )

    # ---------------------------------------------------------
    # 2. Try the fallback model
    # ---------------------------------------------------------

    try:
        return _generate_with_model(
            client=client,
            model=GEMINI_FALLBACK_MODEL,
            prompt=prompt,
            max_attempts=FALLBACK_MAX_ATTEMPTS,
        )

    except ClientError as fallback_error:

        if fallback_error.code == 429:
            raise RuntimeError(
                "Gemini API quota is exhausted for both the "
                f"primary model '{GEMINI_MODEL}' and the "
                f"fallback model '{GEMINI_FALLBACK_MODEL}'."
            ) from fallback_error

        raise

    except ServerError as fallback_error:

        raise RuntimeError(
            "Gemini service is currently unavailable. "
            f"Primary model '{GEMINI_MODEL}' and fallback "
            f"model '{GEMINI_FALLBACK_MODEL}' both failed."
        ) from fallback_error
