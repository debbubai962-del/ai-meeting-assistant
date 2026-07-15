"""
utils/transcript_cleaner.py

Business logic for cleaning, normalizing, and validating raw meeting
transcript text before it is sent to the AI for analysis.

This module has NO Streamlit code. It takes a raw string and returns
a CleaningResult containing the cleaned text plus a report of what
was changed, so the UI layer can display it.
"""

import re
import unicodedata
from dataclasses import dataclass, field


# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------

MIN_VALID_CHARS = 20
MAX_VALID_CHARS = 400_000  # ~ safety ceiling before chunking is required
DUPLICATE_SIMILARITY_MIN_LENGTH = 40  # ignore very short lines for dedup


@dataclass
class QualityIssue:
    """A single validation issue found in the transcript."""
    level: str  # "error" | "warning" | "info"
    message: str


@dataclass
class CleaningResult:
    """Result of cleaning a raw transcript."""
    original_text: str
    cleaned_text: str
    original_char_count: int
    cleaned_char_count: int
    blank_lines_removed: int
    duplicate_paragraphs_removed: int
    speaker_labels_detected: int
    issues: list = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Transcript is usable if there are no 'error' level issues."""
        return not any(issue.level == "error" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.level == "warning" for issue in self.issues)


# -----------------------------------------------------------------------
# Individual cleaning operations
# -----------------------------------------------------------------------

def _normalize_unicode(text: str) -> str:
    """Normalizes unicode characters (smart quotes, odd dashes, etc.)."""
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "\u2018": "'", "\u2019": "'",   # smart single quotes
        "\u201c": '"', "\u201d": '"',   # smart double quotes
        "\u2013": "-", "\u2014": "-",   # en/em dash
        "\u2026": "...",                 # ellipsis
        "\xa0": " ",                     # non-breaking space
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text


def _normalize_line_endings(text: str) -> str:
    """Converts all line endings to \\n."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _collapse_horizontal_whitespace(text: str) -> str:
    """Collapses runs of spaces/tabs within a line to a single space."""
    lines = text.split("\n")
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    return "\n".join(cleaned_lines)


def _remove_excess_blank_lines(text: str) -> tuple[str, int]:
    """
    Collapses 3+ consecutive blank lines down to a single blank line
    (i.e. max one empty line between paragraphs). Returns cleaned text
    and count of blank lines removed.
    """
    lines = text.split("\n")
    original_blank_count = sum(1 for line in lines if line.strip() == "")

    cleaned_lines = []
    blank_streak = 0
    for line in lines:
        if line.strip() == "":
            blank_streak += 1
            if blank_streak <= 1:
                cleaned_lines.append(line)
        else:
            blank_streak = 0
            cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)
    new_blank_count = sum(1 for line in cleaned_lines if line.strip() == "")
    removed = original_blank_count - new_blank_count
    return cleaned_text, removed


def _remove_duplicate_paragraphs(text: str) -> tuple[str, int]:
    """
    Removes exact-duplicate paragraphs (common with bad copy-paste or
    export artifacts). Only paragraphs longer than
    DUPLICATE_SIMILARITY_MIN_LENGTH characters are checked, to avoid
    stripping legitimately repeated short lines like "Yeah." or "Okay.".
    """
    paragraphs = text.split("\n\n")
    seen = set()
    kept_paragraphs = []
    removed_count = 0

    for paragraph in paragraphs:
        normalized = paragraph.strip().lower()
        if len(normalized) >= DUPLICATE_SIMILARITY_MIN_LENGTH:
            if normalized in seen:
                removed_count += 1
                continue
            seen.add(normalized)
        kept_paragraphs.append(paragraph)

    return "\n\n".join(kept_paragraphs), removed_count


def _detect_speaker_labels(text: str) -> int:
    """
    Counts lines that look like speaker labels, e.g. 'John:', 'Speaker 1:',
    'JANE SMITH -'. Used for reporting only; labels are preserved as-is.
    """
    pattern = re.compile(r"^[A-Za-z][A-Za-z0-9 ._'-]{0,40}(:| -)\s")
    lines = text.split("\n")
    return sum(1 for line in lines if pattern.match(line.strip()))


def _rejoin_paragraphs(text: str) -> str:
    """Ensures paragraphs are separated by exactly one blank line."""
    lines = [line for line in text.split("\n")]
    # Collapse any run of 2+ blank lines into exactly one
    result = []
    blank_streak = 0
    for line in lines:
        if line.strip() == "":
            blank_streak += 1
            if blank_streak == 1:
                result.append("")
        else:
            blank_streak = 0
            result.append(line)
    return "\n".join(result).strip()


# -----------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------

def _validate(cleaned_text: str) -> list:
    """Runs quality checks and returns a list of QualityIssue objects."""
    issues = []
    char_count = len(cleaned_text.strip())

    if char_count == 0:
        issues.append(QualityIssue("error", "The transcript is empty after cleaning."))
        return issues

    if char_count < MIN_VALID_CHARS:
        issues.append(QualityIssue(
            "error",
            f"Transcript is too short ({char_count} characters). "
            f"At least {MIN_VALID_CHARS} characters are required."
        ))

    if char_count > MAX_VALID_CHARS:
        issues.append(QualityIssue(
            "warning",
            f"Transcript is very large ({char_count:,} characters). "
            "It may need to be chunked before AI analysis in a later step."
        ))

    word_count = len(cleaned_text.split())
    if 0 < word_count < 15:
        issues.append(QualityIssue(
            "warning",
            "Transcript has very few words. Double-check the full "
            "meeting content was captured."
        ))

    speaker_count = _detect_speaker_labels(cleaned_text)
    if speaker_count == 0:
        issues.append(QualityIssue(
            "info",
            "No speaker labels detected (e.g. 'John:'). This is fine, "
            "but analysis quality improves when speakers are labeled."
        ))

    non_ascii_ratio = sum(1 for c in cleaned_text if ord(c) > 127) / max(char_count, 1)
    if non_ascii_ratio > 0.15:
        issues.append(QualityIssue(
            "info",
            "This transcript contains a significant amount of non-English "
            "or special characters, which may indicate mixed languages."
        ))

    return issues


# -----------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------

def clean_transcript(raw_text: str) -> CleaningResult:
    """
    Runs the full cleaning pipeline on raw transcript text and returns
    a CleaningResult with the cleaned text and a change report.
    """
    original_text = raw_text
    original_char_count = len(raw_text)

    text = _normalize_line_endings(raw_text)
    text = _normalize_unicode(text)
    text = _collapse_horizontal_whitespace(text)
    text, blank_lines_removed = _remove_excess_blank_lines(text)
    text, duplicates_removed = _remove_duplicate_paragraphs(text)
    text = _rejoin_paragraphs(text)

    speaker_count = _detect_speaker_labels(text)
    issues = _validate(text)

    return CleaningResult(
        original_text=original_text,
        cleaned_text=text,
        original_char_count=original_char_count,
        cleaned_char_count=len(text),
        blank_lines_removed=blank_lines_removed,
        duplicate_paragraphs_removed=duplicates_removed,
        speaker_labels_detected=speaker_count,
        issues=issues,
    )