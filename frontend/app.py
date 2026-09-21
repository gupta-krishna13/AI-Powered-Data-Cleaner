import os

import requests
import streamlit as st


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Data Cleaner",
    page_icon="🧹",
    layout="wide",
)


# ---------------------------------------------------------
# UI styling
# ---------------------------------------------------------
# Keep the two main workflow sections visually dominant,
# while keeping their individual recommendation cards compact.
st.markdown(
    """
    <style>
    /* Main section shutters */
    div[class*="st-key-toggle-ai-cleaning-proposal"] button,
    div[class*="st-key-toggle-review-approval"] button {
        min-height: 64px;
        padding: 0.75rem 1rem;
        font-size: 1.25rem;
        font-weight: 700;
        border-width: 1px;
        border-radius: 10px;
    }

    /* Individual recommendation shutters */
    div[class*="st-key-toggle-proposal-card-"] button,
    div[class*="st-key-toggle-approval-card-"] button {
        min-height: 42px;
        padding: 0.45rem 0.75rem;
        font-size: 0.95rem;
        font-weight: 500;
        border-radius: 8px;
    }

    /* Give the two main sections a little more breathing room */
    div[class*="st-key-toggle-ai-cleaning-proposal"],
    div[class*="st-key-toggle-review-approval"] {
        margin-top: 0.35rem;
        margin-bottom: 0.55rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Backend configuration
# ---------------------------------------------------------

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "recommendation_decisions" not in st.session_state:
    st.session_state.recommendation_decisions = {}

if "approval_result" not in st.session_state:
    st.session_state.approval_result = None

if "execution_result" not in st.session_state:
    st.session_state.execution_result = None

if "cleaned_file_bytes" not in st.session_state:
    st.session_state.cleaned_file_bytes = None

if "original_filename" not in st.session_state:
    st.session_state.original_filename = None

if "proposal_section_open" not in st.session_state:
    st.session_state.proposal_section_open = True

if "approval_section_open" not in st.session_state:
    st.session_state.approval_section_open = True

if "proposal_card_open" not in st.session_state:
    st.session_state.proposal_card_open = {}

if "approval_card_open" not in st.session_state:
    st.session_state.approval_card_open = {}


def toggle_session_state(state_key, item_key=None):
    """Toggle a boolean session-state value."""
    if item_key is None:
        st.session_state[state_key] = not st.session_state.get(
            state_key,
            False,
        )
    else:
        state = st.session_state.setdefault(state_key, {})
        state[item_key] = not state.get(item_key, False)


# ---------------------------------------------------------
# Application header
# ---------------------------------------------------------

st.title("🧹 AI Data Cleaner")

st.write(
    "Upload your dataset and let AI analyze its "
    "data-quality issues before recommending cleaning operations."
)


# ---------------------------------------------------------
# File upload
# ---------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls"],
)


# ---------------------------------------------------------
# Analyze dataset
# ---------------------------------------------------------

if uploaded_file is not None:

    st.success(
        f"File selected: {uploaded_file.name}"
    )

    if st.button(
        "🔍 Analyze Dataset",
        type="primary",
    ):

        with st.spinner(
            "Analyzing your dataset..."
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/analyze",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    },
                    timeout=120,
                )

                if response.status_code == 200:

                    st.session_state.analysis_result = (
                        response.json()
                    )

                    # Preserve the actual filename uploaded by the user.
                    # The backend uses a UUID internally, so we must not
                    # use the backend saved filename as the download name.
                    st.session_state.original_filename = (
                        uploaded_file.name
                    )

                    # Reset all previous decisions because this is a new analysis.
                    st.session_state.recommendation_decisions = {}
                    st.session_state.approval_result = None
                    st.session_state.execution_result = None
                    st.session_state.cleaned_file_bytes = None
                    st.session_state.proposal_section_open = True
                    st.session_state.approval_section_open = True
                    st.session_state.proposal_card_open = {}
                    st.session_state.approval_card_open = {}

                    st.success(
                        "Dataset analyzed successfully!"
                    )

                else:

                    st.session_state.analysis_result = None
                    st.session_state.original_filename = None

                    st.error(
                        f"Analysis failed "
                        f"(HTTP {response.status_code})"
                    )

                    try:

                        error_detail = response.json()

                        st.write(
                            error_detail.get(
                                "detail",
                                "Unknown error occurred.",
                            )
                        )

                    except ValueError:

                        st.write(
                            response.text
                        )

            except requests.exceptions.ConnectionError:

                st.session_state.analysis_result = None
                st.session_state.original_filename = None
                st.session_state.recommendation_decisions = {}
                st.session_state.approval_result = None
                st.session_state.execution_result = None
                st.session_state.cleaned_file_bytes = None

                st.error(
                    "Could not connect to the FastAPI backend. "
                    "Make sure Uvicorn is running on "
                    "http://127.0.0.1:8000."
                )

            except requests.exceptions.Timeout:

                st.session_state.analysis_result = None
                st.session_state.original_filename = None
                st.session_state.recommendation_decisions = {}
                st.session_state.approval_result = None
                st.session_state.execution_result = None
                st.session_state.cleaned_file_bytes = None

                st.error(
                    "The analysis request timed out. "
                    "Please try again."
                )

            except requests.exceptions.RequestException as exc:

                st.session_state.analysis_result = None
                st.session_state.original_filename = None
                st.session_state.recommendation_decisions = {}
                st.session_state.approval_result = None
                st.session_state.execution_result = None
                st.session_state.cleaned_file_bytes = None

                st.error(
                    f"Request failed: {str(exc)}"
                )


# ---------------------------------------------------------
# Display analysis results
# ---------------------------------------------------------

if st.session_state.analysis_result is not None:

    result = st.session_state.analysis_result

    profile = result["profile"]
    quality_issues = result["quality_issues"]
    proposal = result["proposal"]


    # -----------------------------------------------------
    # Dataset overview
    # -----------------------------------------------------

    st.divider()

    st.subheader("📊 Dataset Overview")

    missing_values = profile["missing_values"]

    total_missing_values = sum(
        missing_values.values()
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Rows",
            profile["rows"],
        )

    with col2:

        st.metric(
            "Columns",
            profile["columns"],
        )

    with col3:

        st.metric(
            "Missing Values",
            total_missing_values,
        )

    with col4:

        st.metric(
            "Duplicate Rows",
            profile["duplicate_rows"],
        )


    # -----------------------------------------------------
    # Dataset preview
    # -----------------------------------------------------

    st.subheader("👀 Dataset Preview")

    preview = result["preview"]

    if preview:

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No preview data is available."
        )


    # -----------------------------------------------------
    # Dataset structure
    # -----------------------------------------------------

    st.subheader("📋 Dataset Structure")

    structure_col1, structure_col2 = st.columns(2)

    with structure_col1:

        st.write("**Numerical Columns**")

        if profile["numerical_columns"]:

            st.write(
                ", ".join(
                    profile["numerical_columns"]
                )
            )

        else:

            st.write("None")


    with structure_col2:

        st.write("**Categorical Columns**")

        if profile["categorical_columns"]:

            st.write(
                ", ".join(
                    profile["categorical_columns"]
                )
            )

        else:

            st.write("None")


    # -----------------------------------------------------
    # Column details
    # -----------------------------------------------------

    with st.expander("View Column Details"):

        column_details = []

        for column in profile["column_names"]:

            column_details.append(
                {
                    "Column": column,
                    "Data Type": profile["data_types"][column],
                    "Missing Values": profile[
                        "missing_values"
                    ].get(column, 0),
                }
            )

        st.dataframe(
            column_details,
            use_container_width=True,
            hide_index=True,
        )


    # -----------------------------------------------------
    # Quality issues
    # -----------------------------------------------------

    st.divider()

    st.subheader("🔎 Data Quality Issues")


    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    missing_issues = quality_issues[
        "missing_values"
    ]

    if missing_issues:

        st.warning(
            "⚠️ Missing values detected"
        )

        missing_columns = st.columns(
            min(len(missing_issues), 4)
        )

        for index, (column, count) in enumerate(
            missing_issues.items()
        ):

            with missing_columns[
                index % len(missing_columns)
            ]:

                st.metric(
                    column,
                    f"{count} missing",
                )

    else:

        st.success(
            "✅ No missing values detected."
        )


    # -----------------------------------------------------
    # Duplicate rows
    # -----------------------------------------------------

    duplicate_count = quality_issues[
        "duplicate_rows"
    ]

    if duplicate_count > 0:

        st.warning(
            f"⚠️ {duplicate_count} duplicate "
            f"row(s) detected."
        )

    else:

        st.success(
            "✅ No duplicate rows detected."
        )


    # -----------------------------------------------------
    # Potential outliers
    # -----------------------------------------------------

    outlier_issues = quality_issues[
        "potential_outliers"
    ]

    if outlier_issues:

        st.warning(
            "⚠️ Potential numerical outliers detected"
        )

        for column, outlier_info in (
            outlier_issues.items()
        ):

            outlier_count = outlier_info["count"]
            outlier_values = outlier_info["values"]
            lower_bound = outlier_info["lower_bound"]
            upper_bound = outlier_info["upper_bound"]

            with st.container(border=True):

                st.write(
                    f"**{column}** → "
                    f"{outlier_count} potential outlier(s)"
                )

                st.write(
                    f"**Detected Value(s):** "
                    f"{outlier_values}"
                )

                st.write(
                    f"**IQR Bounds:** "
                    f"{lower_bound:.2f} → "
                    f"{upper_bound:.2f}"
                )

                st.caption(
                    "These values are statistically unusual "
                    "according to the IQR method. "
                    "Unusual does not necessarily mean incorrect."
                )

    else:

        st.success(
            "✅ No potential outliers detected."
        )


    # -----------------------------------------------------
    # Inconsistent categories
    # -----------------------------------------------------

    inconsistent_categories = quality_issues[
        "inconsistent_categories"
    ]

    inconsistent_columns = [
        column
        for column, inconsistency
        in inconsistent_categories.items()
        if inconsistency["detected"]
    ]

    if inconsistent_columns:

        st.warning(
            "⚠️ Inconsistent categorical values detected"
        )

        for column in inconsistent_columns:

            inconsistency = inconsistent_categories[
                column
            ]

            groups = inconsistency["groups"]

            st.write(
                f"**{column}**"
            )

            for group in groups:

                st.write(
                    "Equivalent-looking values: "
                    + ", ".join(group)
                )

    else:

        st.success(
            "✅ No inconsistent categorical values detected."
        )


    # -----------------------------------------------------
    # AI cleaning proposal
    # -----------------------------------------------------

    st.divider()

    proposal_is_open = st.session_state.proposal_section_open

    if st.button(
        f"{'▾' if proposal_is_open else '▸'}  🤖 AI Cleaning Proposal",
        key="toggle_ai_cleaning_proposal",
        use_container_width=True,
    ):
        toggle_session_state("proposal_section_open")
        st.rerun()

    if proposal_is_open:

        with st.container(border=True):

            proposal_summary = proposal["summary"]

            st.info(
                f"💡 {proposal_summary}"
            )

            recommendations = proposal["recommendations"]

            if recommendations:

                for index, recommendation in enumerate(recommendations):

                    issue_type = recommendation["issue_type"]
                    operation = recommendation["operation"]
                    columns = recommendation["columns"]
                    affected_values = recommendation["affected_values"]
                    detection_method = recommendation["detection_method"]
                    evidence = recommendation["evidence"]
                    interpretation = recommendation["interpretation"]
                    recommended_action = recommendation["recommended_action"]
                    confidence = recommendation["confidence"]
                    reason = recommendation["reason"]

                    operation_names = {
                        "median_imputation": "Median Imputation",
                        "mode_imputation": "Mode Imputation",
                        "standardization": "Standardization",
                        "remove_outliers": "Review / Remove Outliers",
                        "remove_duplicates": "Review / Remove Duplicate Rows",
                    }

                    operation_icons = {
                        "median_imputation": "📊",
                        "mode_imputation": "🏷️",
                        "standardization": "🔤",
                        "remove_outliers": "📈",
                        "remove_duplicates": "🧹",
                    }

                    operation_name = operation_names.get(operation, operation)
                    operation_icon = operation_icons.get(operation, "🔧")

                    action_display = {
                        "impute": "🛠️ Impute",
                        "standardize": "🔤 Standardize",
                        "review": "👀 Review Before Removal",
                    }

                    action_text = action_display.get(
                        recommended_action,
                        recommended_action.title(),
                    )

                    confidence_display = {
                        "high": "🟢 High",
                        "medium": "🟡 Medium",
                        "low": "🔴 Low",
                    }

                    confidence_text = confidence_display.get(
                        confidence.lower(),
                        confidence.title(),
                    )

                    card_is_open = st.session_state.proposal_card_open.get(
                        index,
                        False,
                    )

                    if st.button(
                        f"{'▾' if card_is_open else '▸'}  {operation_icon} {operation_name}  •  {confidence_text}",
                        key=f"toggle_proposal_card_{index}",
                        use_container_width=True,
                    ):
                        toggle_session_state(
                            "proposal_card_open",
                            index,
                        )
                        st.rerun()

                    if card_is_open:
                        with st.container(border=True):

                            st.write(
                                f"**Issue Type:** {issue_type.replace('_', ' ').title()}"
                            )

                            if columns:
                                st.write("**Affected Column(s)**")
                                st.write(", ".join(columns))
                            else:
                                st.write("**Affected Columns:** Entire row")

                            if affected_values:
                                st.write("**Affected Value(s)**")
                                st.write(
                                    ", ".join(
                                        str(value)
                                        for value in affected_values
                                    )
                                )

                            st.write(
                                f"**Detection Method:** {detection_method}"
                            )

                            st.write("**Evidence**")
                            st.write(evidence)

                            st.write("**Interpretation**")
                            st.write(interpretation)

                            action_col, confidence_col = st.columns(2)

                            with action_col:
                                st.write("**Recommended Action**")
                                st.info(action_text)

                            with confidence_col:
                                st.write("**Confidence**")
                                st.write(confidence_text)

                            st.write("**Why is this recommended?**")
                            st.write(reason)

            else:
                st.success(
                    "✅ AI did not find any cleaning operations "
                    "that require recommendation."
                )

    else:
        recommendations = proposal["recommendations"]

    # -----------------------------------------------------
    # Individual recommendation decisions
    # -----------------------------------------------------

    st.divider()

    approval_is_open = st.session_state.approval_section_open
    decisions = st.session_state.recommendation_decisions

    if st.button(
        f"{'▾' if approval_is_open else '▸'}  👤 Review & Approval",
        key="toggle_review_approval",
        use_container_width=True,
    ):
        toggle_session_state("approval_section_open")
        st.rerun()

    if approval_is_open:

        with st.container(border=True):

            st.write(
                "Review each AI recommendation individually. "
                "No cleaning operation will be executed until "
                "you explicitly choose an action for every recommendation."
            )

            for index, recommendation in enumerate(recommendations):

                recommended_action = recommendation["recommended_action"]
                operation = recommendation["operation"]

                operation_names = {
                    "median_imputation": "Median Imputation",
                    "mode_imputation": "Mode Imputation",
                    "standardization": "Standardization",
                    "remove_outliers": "Review / Remove Outliers",
                    "remove_duplicates": "Review / Remove Duplicate Rows",
                }

                operation_icons = {
                    "median_imputation": "📊",
                    "mode_imputation": "🏷️",
                    "standardization": "🔤",
                    "remove_outliers": "📈",
                    "remove_duplicates": "🧹",
                }

                operation_name = operation_names.get(operation, operation)
                operation_icon = operation_icons.get(operation, "🔧")

                current_decision = decisions.get(index)
                decision_label = {
                    "approve": "✅ Approve",
                    "reject": "❌ Reject",
                    "keep": "🟢 Keep",
                    "remove": "🔴 Remove",
                }.get(
                    current_decision,
                    "⏳ No decision",
                )

                card_is_open = st.session_state.approval_card_open.get(
                    index,
                    False,
                )

                if st.button(
                    f"{'▾' if card_is_open else '▸'}  {operation_icon} {operation_name}  •  {decision_label}",
                    key=f"toggle_approval_card_{index}",
                    use_container_width=True,
                ):
                    toggle_session_state(
                        "approval_card_open",
                        index,
                    )
                    st.rerun()

                if card_is_open:
                    with st.container(border=True):

                        if recommendation["columns"]:
                            st.write("**Affected Column(s)**")
                            st.write(
                                ", ".join(
                                    recommendation["columns"]
                                )
                            )
                        else:
                            st.write(
                                "**Affected Columns:** Entire row"
                            )

                        st.write("**Why is this recommended?**")
                        st.write(recommendation["reason"])

                        if recommended_action != "review":

                            st.write("**Decision**")

                            decision_col1, decision_col2 = st.columns(2)

                            with decision_col1:
                                if st.button(
                                    "✅ Approve",
                                    key=f"approve_recommendation_{index}",
                                    use_container_width=True,
                                ):
                                    decisions[index] = "approve"
                                    st.rerun()

                            with decision_col2:
                                if st.button(
                                    "❌ Reject",
                                    key=f"reject_recommendation_{index}",
                                    use_container_width=True,
                                ):
                                    decisions[index] = "reject"
                                    st.rerun()

                        else:

                            st.warning(
                                "⚠️ This recommendation requires your "
                                "decision before any removal is performed."
                            )

                            st.write("**Decision**")

                            decision_col1, decision_col2 = st.columns(2)

                            with decision_col1:
                                if st.button(
                                    "🟢 Keep",
                                    key=f"keep_recommendation_{index}",
                                    use_container_width=True,
                                ):
                                    decisions[index] = "keep"
                                    st.rerun()

                            with decision_col2:
                                if st.button(
                                    "🔴 Remove",
                                    key=f"remove_recommendation_{index}",
                                    use_container_width=True,
                                ):
                                    decisions[index] = "remove"
                                    st.rerun()

                        current_decision = decisions.get(index)

                        if current_decision == "approve":
                            st.success("Selected decision: ✅ Approve")
                        elif current_decision == "reject":
                            st.info("Selected decision: ❌ Reject")
                        elif current_decision == "keep":
                            st.success("Selected decision: 🟢 Keep")
                        elif current_decision == "remove":
                            st.warning("Selected decision: 🔴 Remove")
                        else:
                            st.info("⏳ No decision selected yet.")

    # -----------------------------------------------------
    # Check whether every recommendation has a decision
    # -----------------------------------------------------

    all_decisions_made = (
        len(decisions)
        == len(recommendations)
    )


    st.divider()


    if recommendations:

        if not all_decisions_made:

            remaining = (
                len(recommendations)
                - len(decisions)
            )

            st.warning(
                f"⏳ Please make a decision for "
                f"{remaining} remaining recommendation(s) "
                "before executing the cleaning."
            )

        else:

            st.success(
                "✅ All recommendations have been reviewed."
            )

            st.write(
                "Only the actions you selected will be "
                "converted into cleaning operations."
            )

            if st.button(
                "🚀 Execute Selected Actions",
                type="primary",
                use_container_width=True,
            ):

                with st.spinner(
                    "Applying your selected cleaning actions..."
                ):

                    try:

                        # -----------------------------------------
                        # Convert Streamlit decisions into API format
                        # -----------------------------------------

                        approval_decisions = [
                            {
                                "recommendation_index": index,
                                "decision": decisions[index],
                            }
                            for index in range(
                                len(recommendations)
                            )
                        ]


                        # -----------------------------------------
                        # Step 1: Approve selected recommendations
                        # -----------------------------------------

                        approval_response = requests.post(
                            f"{BACKEND_URL}/approve",
                            json={
                                "saved_filename": result[
                                    "saved_filename"
                                ],
                                "proposal": proposal,
                                "approval": {
                                    "decisions": approval_decisions
                                },
                            },
                            timeout=30,
                        )


                        if approval_response.status_code != 200:

                            st.error(
                                "Approval failed "
                                f"(HTTP {approval_response.status_code})"
                            )

                            try:

                                error_detail = (
                                    approval_response.json()
                                )

                                st.write(
                                    error_detail.get(
                                        "detail",
                                        "Unknown error occurred.",
                                    )
                                )

                            except ValueError:

                                st.write(
                                    approval_response.text
                                )

                            st.stop()


                        approval_result = (
                            approval_response.json()
                        )

                        st.session_state.approval_result = (
                            approval_result
                        )


                        # -----------------------------------------
                        # Step 2: Execute approved cleaning
                        # -----------------------------------------

                        approval_token = (
                            approval_result[
                                "approval_token"
                            ]
                        )

                        execution_response = requests.post(
                            f"{BACKEND_URL}/execute-cleaning",
                            json={
                                "approval_token": approval_token
                            },
                            timeout=120,
                        )


                        if execution_response.status_code != 200:

                            st.error(
                                "Cleaning execution failed "
                                f"(HTTP {execution_response.status_code})"
                            )

                            try:

                                error_detail = (
                                    execution_response.json()
                                )

                                st.write(
                                    error_detail.get(
                                        "detail",
                                        "Unknown error occurred.",
                                    )
                                )

                            except ValueError:

                                st.write(
                                    execution_response.text
                                )

                            st.stop()


                        execution_result = (
                            execution_response.json()
                        )

                        cleaned_filename = execution_result.get(
                            "cleaned_filename"
                        )

                        if not cleaned_filename:
                            st.error(
                                "Cleaning completed, but the backend "
                                "did not return a cleaned filename."
                            )
                            st.stop()

                        # Fetch the cleaned file once after successful execution.
                        # Cache the bytes so normal Streamlit reruns do not make
                        # another HTTP request to the backend.
                        download_url = (
                            f"{BACKEND_URL}/download/"
                            f"{cleaned_filename}"
                        )

                        download_response = requests.get(
                            download_url,
                            timeout=30,
                        )

                        if download_response.status_code != 200:
                            st.error(
                                "Cleaning completed, but the cleaned "
                                "dataset could not be retrieved."
                            )
                            st.stop()

                        st.session_state.execution_result = (
                            execution_result
                        )
                        st.session_state.cleaned_file_bytes = (
                            download_response.content
                        )

                        st.rerun()


                    except requests.exceptions.ConnectionError:

                        st.session_state.analysis_result = None
                        st.session_state.original_filename = None
                        st.session_state.recommendation_decisions = {}
                        st.session_state.approval_result = None
                        st.session_state.execution_result = None
                        st.session_state.cleaned_file_bytes = None

                        st.error(
                            "Could not connect to the FastAPI backend. "
                            "Make sure Uvicorn is running on "
                                                "http://127.0.0.1:8000."
                        )

                    except requests.exceptions.Timeout:

                        st.session_state.analysis_result = None
                        st.session_state.original_filename = None
                        st.session_state.recommendation_decisions = {}
                        st.session_state.approval_result = None
                        st.session_state.execution_result = None
                        st.session_state.cleaned_file_bytes = None

                        st.error(
                            "The analysis request timed out. "
                            "Please try again."
                        )

                    except requests.exceptions.RequestException as exc:

                        st.session_state.analysis_result = None
                        st.session_state.original_filename = None
                        st.session_state.recommendation_decisions = {}
                        st.session_state.approval_result = None
                        st.session_state.execution_result = None
                        st.session_state.cleaned_file_bytes = None

                        st.error(
                            f"Request failed: {str(exc)}"
                        )


    # -----------------------------------------------------
    # Cleaning execution result
    # -----------------------------------------------------

    if st.session_state.execution_result is not None:

        execution_result = (
            st.session_state.execution_result
        )

        st.divider()

        st.subheader("🎉 Cleaning Completed")

        st.success(
            execution_result.get(
                "message",
                "Cleaning completed successfully.",
            )
        )

        report = execution_result.get(
            "report",
            {}
        )

        st.write("### 📊 Cleaning Report")

        report_col1, report_col2, report_col3, report_col4 = (
            st.columns(4)
        )

        with report_col1:

            st.metric(
                "Rows Before",
                report.get(
                    "rows_before",
                    0,
                ),
            )

        with report_col2:

            st.metric(
                "Rows After",
                report.get(
                    "rows_after",
                    0,
                ),
            )

        with report_col3:

            st.metric(
                "Rows Removed",
                report.get(
                    "rows_removed",
                    0,
                ),
            )

        with report_col4:

            st.metric(
                "Duplicates Removed",
                report.get(
                    "duplicates_removed",
                    0,
                ),
            )


        st.write("### 🔍 Cleaning Audit")

        audit = execution_result.get(
            "audit",
            {}
        )

        st.json(audit)


        cleaned_filename = execution_result.get(
            "cleaned_filename"
        )

        # The backend keeps a UUID-based filename internally so that
        # processed files remain unique. The browser should show the
        # actual filename uploaded by the user.
        original_filename = (
            st.session_state.original_filename
            or "dataset.csv"
        )

        original_stem = os.path.splitext(
            original_filename
        )[0]

        download_filename = (
            f"{original_stem}_cleaned.csv"
        )

        cleaned_file_bytes = (
            st.session_state.cleaned_file_bytes
        )

        if cleaned_filename and cleaned_file_bytes is not None:

            st.download_button(
                label="⬇️ Download Cleaned Dataset",
                data=cleaned_file_bytes,
                file_name=download_filename,
                mime="text/csv",
                use_container_width=True,
            )

        elif cleaned_filename:

            st.warning(
                "The cleaned file is available, but its download "
                "data is not currently cached. Please run the cleaning "
                "operation again if the download button does not appear."
            )

