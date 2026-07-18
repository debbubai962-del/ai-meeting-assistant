"""
components/metadata_section.py

UI component for collecting meeting metadata (type, date, participants,
organizer, duration, department, priority) via a form. Validates input
using utils/metadata_validator.py and returns a structured dict.
"""

from datetime import date

import streamlit as st

from utils.metadata_validator import (
    MEETING_TYPES,
    PRIORITY_LEVELS,
    parse_participants,
    validate_metadata,
)


def render_metadata_section() -> dict | None:
    """
    Renders the meeting metadata form.

    Returns:
        A dict of validated metadata if the form was submitted and
        passed validation, otherwise None.
    """
    with st.form(key="metadata_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            meeting_title = st.text_input(
                label="Meeting Title",
                placeholder="e.g. Q3 Product Roadmap Review",
            )
            meeting_type = st.selectbox(
                label="Meeting Type",
                options=MEETING_TYPES,
                index=0,
            )
            meeting_date = st.date_input(
                label="Meeting Date",
                value=date.today(),
            )
            duration_minutes = st.number_input(
                label="Duration (minutes)",
                min_value=0,
                max_value=600,
                value=30,
                step=5,
            )

        with col2:
            organizer = st.text_input(
                label="Organizer / Facilitator",
                placeholder="e.g. Priya Sharma",
            )
            department = st.text_input(
                label="Department / Team",
                placeholder="e.g. Product, Sales, Engineering",
            )
            priority = st.selectbox(
                label="Priority Level",
                options=PRIORITY_LEVELS,
                index=1,
            )
            participants_raw = st.text_area(
                label="Participants",
                placeholder="Comma or line separated: Priya Sharma, John Doe, Maria Lopez",
                height=100,
            )

        submitted = st.form_submit_button(
            "Confirm Meeting Details",
            use_container_width=True,
            type="primary",
        )

    if not submitted:
        # Show previously confirmed metadata (if any) so it persists
        # across reruns until the user resubmits.
        existing = st.session_state.get("meeting_metadata")
        return existing

    participants = parse_participants(participants_raw)

    result = validate_metadata(
        meeting_title=meeting_title,
        meeting_type=meeting_type,
        meeting_date=meeting_date,
        organizer=organizer,
        participants=participants,
        duration_minutes=int(duration_minutes),
        department=department,
        priority=priority,
    )

    for error in result.errors:
        st.error(f"🛑 {error}")

    for warning in result.warnings:
        st.warning(f"⚠️ {warning}")

    if not result.is_valid:
        return None

    if result.warnings:
        st.info("Details saved with warnings above. You may proceed or refine them.")
    else:
        st.success("✅ Meeting details confirmed.")

    metadata = {
        "meeting_title": meeting_title.strip(),
        "meeting_type": meeting_type,
        "meeting_date": meeting_date.isoformat(),
        "organizer": organizer.strip(),
        "department": department.strip(),
        "priority": priority,
        "duration_minutes": int(duration_minutes),
        "participants": participants,
    }

    return metadata


def render_metadata_summary(metadata: dict) -> None:
    """Renders a compact read-only summary of confirmed metadata."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Meeting Type", value=metadata["meeting_type"])
    with col2:
        st.metric(label="Priority", value=metadata["priority"])
    with col3:
        st.metric(label="Participants", value=len(metadata["participants"]))

    st.caption(
        f"**{metadata['meeting_title']}** · {metadata['meeting_date']} · "
        f"{metadata['duration_minutes']} min · "
        f"Organized by {metadata['organizer'] or 'Not specified'}"
        + (f" · {metadata['department']}" if metadata["department"] else "")
    )

    if metadata["participants"]:
        st.caption("Participants: " + ", ".join(metadata["participants"]))