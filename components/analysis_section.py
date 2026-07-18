"""
components/analysis_section.py

UI component that triggers AI analysis of the cleaned transcript and
metadata, shows loading/progress state, and surfaces any errors.
"""

import streamlit as st

from utils.ai_client import run_meeting_analysis


def render_analysis_section(cleaned_text: str, metadata: dict) -> dict | None:
    """
    Renders the 'Run AI Analysis' trigger and handles the request.

    Returns:
        The structured analysis dict if a successful analysis exists
        in session state, otherwise None.
    """
    existing_result = st.session_state.get("analysis_result")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(
            "This sends the cleaned transcript and meeting details to "
            "the AI model for structured business analysis."
        )
    with col2:
        run_clicked = st.button(
            "🚀 Run AI Analysis",
            use_container_width=True,
            type="primary",
        )

    if run_clicked:
        with st.spinner("Analyzing transcript... this may take up to a minute."):
            result = run_meeting_analysis(cleaned_text, metadata)

        if result.success:
            st.session_state["analysis_result"] = result.data
            st.success("✅ Analysis complete.")
            return result.data
        else:
            st.session_state["analysis_result"] = None
            st.error(f"🛑 {result.error_message}")
            return None

    if existing_result:
        st.info("Showing results from the last analysis run. Click the button above to re-run.")
        return existing_result

    return None