"""
components/cleaning_section.py

UI component that runs the transcript cleaning pipeline, displays a
change report, a before/after preview, and any quality warnings.

Returns the cleaned transcript text if it passes validation, otherwise
returns None so the pipeline cannot proceed with invalid input.
"""

import streamlit as st

from utils.transcript_cleaner import clean_transcript


ISSUE_ICONS = {
    "error": "🛑",
    "warning": "⚠️",
    "info": "ℹ️",
}


def render_cleaning_section(raw_transcript_text: str) -> str | None:
    """
    Renders the cleaning & validation UI for a given raw transcript.

    Args:
        raw_transcript_text: the raw text captured in the upload step.

    Returns:
        The cleaned transcript text if valid, otherwise None.
    """
    result = clean_transcript(raw_transcript_text)

    # -----------------------------------------------------------------
    # Change summary metrics
    # -----------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        char_delta = result.cleaned_char_count - result.original_char_count
        st.metric(
            label="Characters",
            value=f"{result.cleaned_char_count:,}",
            delta=f"{char_delta:,}",
        )
    with col2:
        st.metric(label="Blank Lines Removed", value=result.blank_lines_removed)
    with col3:
        st.metric(label="Duplicates Removed", value=result.duplicate_paragraphs_removed)
    with col4:
        st.metric(label="Speaker Labels Found", value=result.speaker_labels_detected)

    # -----------------------------------------------------------------
    # Quality issues
    # -----------------------------------------------------------------
    if result.issues:
        st.markdown("**Quality Checks**")
        for issue in result.issues:
            icon = ISSUE_ICONS.get(issue.level, "•")
            if issue.level == "error":
                st.error(f"{icon} {issue.message}")
            elif issue.level == "warning":
                st.warning(f"{icon} {issue.message}")
            else:
                st.info(f"{icon} {issue.message}")
    else:
        st.success("✅ No quality issues detected.")

    # -----------------------------------------------------------------
    # Before / after preview
    # -----------------------------------------------------------------
    st.markdown("**Preview**")
    tab_before, tab_after = st.tabs(["Original", "Cleaned"])

    with tab_before:
        st.text(result.original_text[:3000])
        if len(result.original_text) > 3000:
            st.caption("Preview truncated at 3,000 characters.")

    with tab_after:
        st.text(result.cleaned_text[:3000])
        if len(result.cleaned_text) > 3000:
            st.caption("Preview truncated at 3,000 characters.")

    # -----------------------------------------------------------------
    # Gate: only return cleaned text if valid
    # -----------------------------------------------------------------
    if not result.is_valid:
        st.error(
            "This transcript cannot proceed until the errors above are "
            "resolved. Please go back and provide a longer or more "
            "complete transcript."
        )
        return None

    return result.cleaned_text