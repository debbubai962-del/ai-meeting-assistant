"""
prompts/meeting_analysis_prompt.py

Prompt templates for meeting transcript analysis. Kept isolated from
business logic so prompts can be tuned independently.
"""

JSON_SCHEMA_DESCRIPTION = """
Return ONLY a valid JSON object (no markdown, no code fences, no commentary)
with exactly this structure:

{
  "executive_summary": "string, 2-4 sentences, C-suite level overview",
  "detailed_summary": "string, comprehensive paragraph-form summary",
  "meeting_sentiment": "one of: Positive, Neutral, Negative, Mixed",
  "overall_priority_level": "one of: Low, Medium, High, Critical",
  "decisions_taken": ["string", "..."],
  "action_items": [
    {
      "task": "string, clear description",
      "owner": "string, person name if mentioned, else empty string",
      "team": "string, responsible team/department if inferable, else empty string",
      "deadline": "string, date or timeframe if mentioned, else empty string",
      "priority": "one of: Low, Medium, High, Critical"
    }
  ],
  "risks": ["string", "..."],
  "opportunities": ["string", "..."],
  "blockers": ["string", "..."],
  "open_questions": ["string", "..."],
  "kpi_mentions": ["string", "..."],
  "budget_mentions": ["string", "..."],
  "timeline_mentions": ["string", "..."],
  "compliance_issues": ["string", "..."],
  "escalations": ["string", "..."],
  "key_business_insights": ["string", "..."],
  "suggested_next_steps": ["string", "..."],
  "next_meeting_agenda": ["string", "..."],
  "follow_up_email": {
    "subject": "string",
    "body": "string, professional email body with greeting and sign-off"
  }
}

Rules:
- If a category has no relevant content in the transcript, return an empty array [] (not null, not omitted).
- Never invent facts, names, numbers, or dates that are not supported by the transcript.
- "owner" and "team" in action_items should be left as empty strings if not explicitly mentioned or clearly inferable.
- Keep all string values concise and professional, suitable for an executive audience.
- Output must be valid, parseable JSON and nothing else.
"""


def build_system_prompt() -> str:
    """Returns the system prompt establishing the AI's role and constraints."""
    return (
        "You are a senior business analyst at a top-tier consulting firm "
        "(Deloitte/McKinsey caliber). You analyze meeting transcripts and "
        "produce structured, accurate, executive-ready business intelligence. "
        "You are precise, never fabricate information, and always ground "
        "your output strictly in what was actually said in the transcript. "
        + JSON_SCHEMA_DESCRIPTION
    )


def build_user_prompt(transcript_text: str, metadata: dict) -> str:
    """
    Builds the user-facing prompt combining metadata context and the
    cleaned transcript.
    """
    participants = ", ".join(metadata.get("participants", [])) or "Not specified"

    metadata_block = (
        f"Meeting Title: {metadata.get('meeting_title', 'Not specified')}\n"
        f"Meeting Type: {metadata.get('meeting_type', 'Not specified')}\n"
        f"Date: {metadata.get('meeting_date', 'Not specified')}\n"
        f"Duration: {metadata.get('duration_minutes', 'Not specified')} minutes\n"
        f"Organizer: {metadata.get('organizer') or 'Not specified'}\n"
        f"Department/Team: {metadata.get('department') or 'Not specified'}\n"
        f"Stated Priority: {metadata.get('priority', 'Not specified')}\n"
        f"Participants: {participants}"
    )

    return (
        f"MEETING METADATA:\n{metadata_block}\n\n"
        f"TRANSCRIPT:\n{transcript_text}\n\n"
        f"Analyze this meeting transcript and produce the structured JSON "
        f"output as instructed."
    )