"""
utils/metadata_validator.py

Business logic for validating meeting metadata collected from the user
before it is attached to the transcript for AI analysis.

This module has NO Streamlit code.
"""

from dataclasses import dataclass, field
from datetime import date


MEETING_TYPES = [
    "Business Meeting",
    "Client Meeting",
    "HR Meeting",
    "Sprint Planning",
    "Sales Meeting",
    "Executive Meeting",
    "Project Review",
    "Stakeholder Meeting",
    "Other",
]

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]

MAX_TITLE_LENGTH = 150
MAX_PARTICIPANTS = 50


@dataclass
class MetadataValidationResult:
    """Result of validating meeting metadata."""
    is_valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def parse_participants(raw_participants: str) -> list:
    """
    Splits a comma or newline separated participants string into a
    clean list of names, removing empty entries and duplicates while
    preserving order.
    """
    if not raw_participants:
        return []

    raw_participants = raw_participants.replace("\n", ",")
    candidates = [name.strip() for name in raw_participants.split(",")]

    seen = set()
    cleaned = []
    for name in candidates:
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(name)

    return cleaned


def validate_metadata(
    meeting_title: str,
    meeting_type: str,
    meeting_date: date,
    organizer: str,
    participants: list,
    duration_minutes: int,
    department: str,
    priority: str,
) -> MetadataValidationResult:
    """
    Validates a full metadata set and returns a MetadataValidationResult
    with any errors (blocking) or warnings (non-blocking).
    """
    errors = []
    warnings = []

    if not meeting_title or not meeting_title.strip():
        errors.append("Meeting title is required.")
    elif len(meeting_title) > MAX_TITLE_LENGTH:
        errors.append(
            f"Meeting title must be under {MAX_TITLE_LENGTH} characters."
        )

    if meeting_type not in MEETING_TYPES:
        errors.append("Please select a valid meeting type.")

    if meeting_date is None:
        errors.append("Meeting date is required.")
    elif meeting_date > date.today():
        warnings.append(
            "Meeting date is in the future. Please confirm this is correct."
        )

    if not organizer or not organizer.strip():
        warnings.append(
            "No organizer specified. Adding one improves report quality."
        )

    if not participants:
        warnings.append(
            "No participants listed. Adding names helps the AI assign "
            "action items to the right people."
        )
    elif len(participants) > MAX_PARTICIPANTS:
        errors.append(
            f"Too many participants listed (max {MAX_PARTICIPANTS})."
        )

    if duration_minutes is not None and duration_minutes <= 0:
        errors.append("Meeting duration must be greater than zero.")

    if not department or not department.strip():
        warnings.append(
            "No department/team specified. This is optional but helpful "
            "for routing action items."
        )

    if priority not in PRIORITY_LEVELS:
        errors.append("Please select a valid priority level.")

    return MetadataValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )