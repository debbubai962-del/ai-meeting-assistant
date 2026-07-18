"""
utils/ai_client.py

Business logic for calling the OpenRouter API (via the OpenAI SDK) to
run structured meeting analysis. This module has NO Streamlit code.

Handles: missing API key, timeouts, rate limits, network failures,
invalid/malformed JSON responses, and oversized transcripts.
"""

import json
from dataclasses import dataclass, field

from openai import (
    OpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

from config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from prompts.meeting_analysis_prompt import build_system_prompt, build_user_prompt

MAX_TRANSCRIPT_CHARS = 60_000  # ~ safety ceiling; larger needs chunking (future step)
REQUEST_TIMEOUT_SECONDS = 90

REQUIRED_LIST_FIELDS = [
    "decisions_taken", "risks", "opportunities", "blockers", "open_questions",
    "kpi_mentions", "budget_mentions", "timeline_mentions", "compliance_issues",
    "escalations", "key_business_insights", "suggested_next_steps",
    "next_meeting_agenda",
]


@dataclass
class AnalysisResult:
    """Result of an AI meeting analysis request."""
    success: bool
    data: dict = field(default_factory=dict)
    error_message: str = ""


def _get_client() -> OpenAI:
    """Creates an OpenAI-SDK client pointed at the OpenRouter endpoint."""
    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def _strip_code_fences(text: str) -> str:
    """Removes ```json / ``` wrapping if the model added it despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _normalize_result(data: dict) -> dict:
    """
    Ensures all expected fields exist with sensible defaults, so the UI
    layer never has to guard against missing keys.
    """
    data.setdefault("executive_summary", "")
    data.setdefault("detailed_summary", "")
    data.setdefault("meeting_sentiment", "Neutral")
    data.setdefault("overall_priority_level", "Medium")
    data.setdefault("action_items", [])
    data.setdefault("follow_up_email", {"subject": "", "body": ""})

    for field_name in REQUIRED_LIST_FIELDS:
        if field_name not in data or not isinstance(data[field_name], list):
            data[field_name] = []

    if not isinstance(data.get("action_items"), list):
        data["action_items"] = []

    normalized_items = []
    for item in data["action_items"]:
        if not isinstance(item, dict):
            continue
        normalized_items.append({
            "task": item.get("task", ""),
            "owner": item.get("owner", ""),
            "team": item.get("team", ""),
            "deadline": item.get("deadline", ""),
            "priority": item.get("priority", "Medium"),
        })
    data["action_items"] = normalized_items

    if not isinstance(data.get("follow_up_email"), dict):
        data["follow_up_email"] = {"subject": "", "body": ""}
    else:
        data["follow_up_email"].setdefault("subject", "")
        data["follow_up_email"].setdefault("body", "")

    return data


def run_meeting_analysis(transcript_text: str, metadata: dict) -> AnalysisResult:
    """
    Sends the transcript and metadata to the AI model and returns a
    structured AnalysisResult. Never raises — all failure modes are
    caught and returned as a user-friendly error_message.
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.strip() == "your_openrouter_api_key_here":
        return AnalysisResult(
            success=False,
            error_message=(
                "OpenRouter API key is not configured. Please add your "
                "key to the .env file as OPENROUTER_API_KEY=sk-or-..."
            ),
        )

    if not transcript_text or not transcript_text.strip():
        return AnalysisResult(
            success=False,
            error_message="No transcript text was provided for analysis.",
        )

    if len(transcript_text) > MAX_TRANSCRIPT_CHARS:
        return AnalysisResult(
            success=False,
            error_message=(
                f"Transcript is too long ({len(transcript_text):,} characters). "
                f"The current limit is {MAX_TRANSCRIPT_CHARS:,} characters. "
                "Chunking support for very long transcripts is planned for "
                "a future update."
            ),
        )

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": build_user_prompt(transcript_text, metadata)},
            ],
            temperature=0.3,
            max_tokens=4000,
        )

    except APITimeoutError:
        return AnalysisResult(
            success=False,
            error_message=(
                "The AI request timed out. This can happen with very long "
                "transcripts or a slow connection. Please try again."
            ),
        )
    except RateLimitError:
        return AnalysisResult(
            success=False,
            error_message=(
                "Rate limit reached on your OpenRouter account. Please "
                "wait a moment and try again, or check your OpenRouter "
                "usage limits."
            ),
        )
    except APIConnectionError:
        return AnalysisResult(
            success=False,
            error_message=(
                "Could not connect to OpenRouter. Please check your "
                "internet connection and try again."
            ),
        )
    except APIStatusError as exc:
        status_code = getattr(exc, "status_code", "unknown")
        return AnalysisResult(
            success=False,
            error_message=(
                f"OpenRouter returned an error (status {status_code}). "
                "This may mean your API key is invalid, out of credits, "
                "or the selected model is unavailable."
            ),
        )
    except Exception as exc:  # noqa: BLE001 - final safety net, never crash the app
        return AnalysisResult(
            success=False,
            error_message=f"An unexpected error occurred while contacting the AI: {exc}",
        )

    try:
        raw_content = response.choices[0].message.content
        cleaned_content = _strip_code_fences(raw_content)
        parsed = json.loads(cleaned_content)
    except (json.JSONDecodeError, IndexError, AttributeError, TypeError):
        return AnalysisResult(
            success=False,
            error_message=(
                "The AI response could not be parsed as valid JSON. "
                "Please try running the analysis again."
            ),
        )

    if not isinstance(parsed, dict):
        return AnalysisResult(
            success=False,
            error_message="The AI response was not in the expected format. Please try again.",
        )

    normalized = _normalize_result(parsed)

    return AnalysisResult(success=True, data=normalized)