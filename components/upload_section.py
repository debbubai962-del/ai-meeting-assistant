"""
components/upload_section.py

UI component for getting a meeting transcript into the app, either by
file upload (.txt, .docx, .pdf) or by pasting text directly.

Returns the raw transcript text (or None if not yet provided) so the
caller (app.py) can store it in session state and pass it to later
pipeline steps (cleaning, metadata, AI analysis).
"""

import streamlit as st

from utils.transcript_reader import read_transcript_file, TranscriptReadError

MAX_FILE_SIZE_MB = 15
MIN_TRANSCRIPT_CHARS = 20


def _validate_size(file_bytes: bytes, filename: str) -> bool:
    """Checks the uploaded file isn't unreasonably large. Returns True if OK."""
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        st.error(
            f"'{filename}' is {size_mb:.1f} MB, which exceeds the "
            f"{MAX_FILE_SIZE_MB} MB limit. Please upload a smaller file."
        )
        return False
    return True


def render_upload_section() -> str | None:
    """
    Renders the transcript input UI (upload + paste tabs).

    Returns:
        The transcript text as a string if successfully provided,
        otherwise None.
    """
    st.subheader("1. Provide Your Meeting Transcript")

    tab_upload, tab_paste = st.tabs(["📁 Upload File", "📋 Paste Text"])

    transcript_text: str | None = None

    # ---------------------------------------------------------------
    # Tab 1: File upload
    # ---------------------------------------------------------------
    with tab_upload:
        st.caption("Supported formats: .txt, .docx, .pdf")

        uploaded_file = st.file_uploader(
            label="Upload transcript file",
            type=["txt", "docx", "pdf"],
            accept_multiple_files=False,
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()

            if _validate_size(file_bytes, uploaded_file.name):
                try:
                    with st.spinner(f"Reading '{uploaded_file.name}'..."):
                        result = read_transcript_file(
                            filename=uploaded_file.name,
                            file_bytes=file_bytes,
                        )
                    transcript_text = result.text
                    st.success(
                        f"Loaded '{result.filename}' "
                        f"({result.char_count:,} characters, "
                        f".{result.file_type.upper()})"
                    )
                    with st.expander("Preview extracted text"):
                        st.text(result.text[:2000])
                        if len(result.text) > 2000:
                            st.caption("Preview truncated at 2,000 characters.")

                except TranscriptReadError as err:
                    st.error(str(err))

    # ---------------------------------------------------------------
    # Tab 2: Paste text
    # ---------------------------------------------------------------
    with tab_paste:
        st.caption("Paste your meeting transcript below")

        pasted_text = st.text_area(
            label="Paste transcript",
            height=280,
            placeholder=(
                "Speaker 1: Let's start with the Q3 roadmap review...\n"
                "Speaker 2: Sure, first let's cover the blockers..."
            ),
            label_visibility="collapsed",
        )

        if pasted_text and pasted_text.strip():
            transcript_text = pasted_text
            st.success(f"Transcript ready ({len(pasted_text):,} characters)")

    # ---------------------------------------------------------------
    # Minimum length validation (applies to either source)
    # ---------------------------------------------------------------
    if transcript_text is not None and len(transcript_text.strip()) < MIN_TRANSCRIPT_CHARS:
        st.warning(
            "This transcript looks very short. Please double-check "
            "that the full content was captured."
        )

    return transcript_text