"""
app.py

Entry point for the AI Business Meeting Assistant.
"""

import streamlit as st

from config.settings import (
    APP_NAME,
    APP_VERSION,
    is_api_key_configured,
)
from components.upload_section import render_upload_section
from components.cleaning_section import render_cleaning_section
from components.metadata_section import render_metadata_section, render_metadata_summary
from components.analysis_section import render_analysis_section
from components.results_display import render_results_display
from components.export_section import render_export_section
from components.ui_helpers import (
    load_css,
    render_header,
    render_progress_stepper,
    render_section_header,
    render_sidebar_stats,
    render_footer,
)


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### 🗂️ {APP_NAME}")
        st.caption(f"Version {APP_VERSION}")
        st.divider()

        st.markdown("**Environment Status**")
        with st.container(border=True):
            if is_api_key_configured():
                st.success("OpenRouter API key: configured", icon="✅")
            else:
                st.warning("OpenRouter API key: not configured", icon="⚠️")
                st.caption(
                    "Add OPENROUTER_API_KEY to your .env file to "
                    "enable AI analysis."
                )

        st.divider()

        render_sidebar_stats(
            st.session_state.get("cleaned_transcript_text")
            or st.session_state.get("transcript_text")
        )

        st.divider()
        st.markdown("**Build Progress**")
        st.caption("Step 6 of 6 — Report & Export")

        st.divider()

        with st.expander("Need help?"):
            st.caption(
                "Upload a transcript, confirm meeting details, run AI "
                "analysis, then export the report as PDF, Word, Markdown, "
                "or plain text."
            )

        st.divider()
        render_footer()


def render_main_area() -> None:
    render_header()

    transcript_text = st.session_state.get("transcript_text")
    cleaned_text = st.session_state.get("cleaned_transcript_text")
    metadata = st.session_state.get("meeting_metadata")
    analysis_result = st.session_state.get("analysis_result")

    # Determine which step is active for the progress tracker
    if analysis_result:
        current_step = 5  # Report & Export
    elif metadata:
        current_step = 4  # AI Analysis
    elif cleaned_text:
        current_step = 3  # Metadata
    elif transcript_text:
        current_step = 2  # Cleaning & Validation
    else:
        current_step = 1  # Transcript Input

    render_progress_stepper(current_step_index=current_step)

    if not is_api_key_configured():
        st.warning(
            "OpenRouter API key is not configured yet. You can complete "
            "the earlier steps, but AI analysis will not work until you "
            "add your key to .env."
        )

    # -----------------------------------------------------------------
    # Card 1: Transcript input
    # -----------------------------------------------------------------
    with st.container(border=True):
        render_section_header(
            icon="📄",
            title="Provide Your Meeting Transcript",
            description="Upload a file or paste text to begin analysis",
        )
        transcript_text = render_upload_section()

    st.session_state["transcript_text"] = transcript_text

    # -----------------------------------------------------------------
    # Card 2: Cleaning & validation
    # -----------------------------------------------------------------
    cleaned_text = None
    if transcript_text:
        st.divider()
        with st.container(border=True):
            render_section_header(
                icon="🧹",
                title="Cleaning & Validation",
                description="Normalizing formatting and checking transcript quality",
            )
            cleaned_text = render_cleaning_section(transcript_text)

    st.session_state["cleaned_transcript_text"] = cleaned_text

    # -----------------------------------------------------------------
    # Card 3: Meeting metadata
    # -----------------------------------------------------------------
    metadata = None
    if cleaned_text:
        st.divider()
        with st.container(border=True):
            render_section_header(
                icon="🗒️",
                title="Meeting Metadata",
                description="Add context to improve the quality of AI analysis",
            )
            metadata = render_metadata_section()

    st.session_state["meeting_metadata"] = metadata

    # -----------------------------------------------------------------
    # Card 4: AI Analysis trigger
    # -----------------------------------------------------------------
    analysis_result = None
    if cleaned_text and metadata:
        st.divider()
        with st.container(border=True):
            render_section_header(
                icon="🤖",
                title="AI Business Analysis",
                description="Generate an executive-ready report from this meeting",
            )
            analysis_result = render_analysis_section(cleaned_text, metadata)

    st.session_state["analysis_result"] = analysis_result

    # -----------------------------------------------------------------
    # Card 5: Results dashboard
    # -----------------------------------------------------------------
    if analysis_result:
        st.divider()
        with st.container(border=True):
            render_section_header(
                icon="📊",
                title="Meeting Analysis Report",
                description="Structured business intelligence generated from this meeting",
            )
            render_results_display(analysis_result)

        # -------------------------------------------------------------
        # Card 6: Export
        # -------------------------------------------------------------
        st.divider()
        with st.container(border=True):
            render_section_header(
                icon="📤",
                title="Export Report",
                description="Download this report to share with your team",
            )
            render_export_section(analysis_result, metadata)


def main() -> None:
    render_sidebar()
    render_main_area()


if __name__ == "__main__":
    main()