"""
components/export_section.py

UI component for exporting the AI analysis report as TXT, Markdown,
DOCX, or PDF.
"""

import streamlit as st

from utils.report_exporter import (
    build_txt,
    build_markdown,
    build_docx,
    build_pdf,
    build_report_filename,
)


def render_export_section(data: dict, metadata: dict) -> None:
    """Renders format selection and a download button for the report."""

    format_choice = st.radio(
        label="Choose export format",
        options=["PDF", "DOCX (Word)", "Markdown", "Plain Text"],
        horizontal=True,
    )

    try:
        if format_choice == "PDF":
            file_bytes = build_pdf(data, metadata)
            filename = build_report_filename(metadata, "pdf")
            mime = "application/pdf"

        elif format_choice == "DOCX (Word)":
            file_bytes = build_docx(data, metadata)
            filename = build_report_filename(metadata, "docx")
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        elif format_choice == "Markdown":
            text_content = build_markdown(data, metadata)
            file_bytes = text_content.encode("utf-8")
            filename = build_report_filename(metadata, "md")
            mime = "text/markdown"

        else:  # Plain Text
            text_content = build_txt(data, metadata)
            file_bytes = text_content.encode("utf-8")
            filename = build_report_filename(metadata, "txt")
            mime = "text/plain"

    except Exception as exc:  # noqa: BLE001 - never crash the app on export failure
        st.error(f"🛑 Could not generate the export file: {exc}")
        return

    st.download_button(
        label=f"⬇️ Download {format_choice}",
        data=file_bytes,
        file_name=filename,
        mime=mime,
        use_container_width=True,
        type="primary",
    )

    st.caption(f"File will be saved as: `{filename}`")