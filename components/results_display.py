"""
components/results_display.py

UI component that renders the structured AI analysis result in a
tabbed, dashboard-style layout.
"""

import streamlit as st


SENTIMENT_COLORS = {
    "Positive": "🟢",
    "Neutral": "🟡",
    "Negative": "🔴",
    "Mixed": "🟠",
}

PRIORITY_ICONS = {
    "Low": "🔵",
    "Medium": "🟡",
    "High": "🟠",
    "Critical": "🔴",
}


def _render_bullet_list(items: list, empty_message: str) -> None:
    if not items:
        st.caption(empty_message)
        return
    for item in items:
        st.markdown(f"- {item}")


def render_results_display(data: dict) -> None:
    """Renders the full structured analysis result."""

    # -----------------------------------------------------------------
    # Top summary strip
    # -----------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        sentiment = data.get("meeting_sentiment", "Neutral")
        st.metric(
            label="Meeting Sentiment",
            value=f"{SENTIMENT_COLORS.get(sentiment, '⚪')} {sentiment}",
        )
    with col2:
        priority = data.get("overall_priority_level", "Medium")
        st.metric(
            label="Overall Priority",
            value=f"{PRIORITY_ICONS.get(priority, '⚪')} {priority}",
        )
    with col3:
        st.metric(label="Action Items", value=len(data.get("action_items", [])))

    st.divider()

    st.markdown("### Executive Summary")
    st.write(data.get("executive_summary") or "Not available.")

    tabs = st.tabs([
        "📋 Summary",
        "✅ Action Items",
        "⚠️ Risks & Blockers",
        "💡 Insights",
        "📊 Business Signals",
        "✉️ Follow-Up",
    ])

    # Tab 1: Summary
    with tabs[0]:
        st.markdown("**Detailed Summary**")
        st.write(data.get("detailed_summary") or "Not available.")

        st.markdown("**Decisions Taken**")
        _render_bullet_list(data.get("decisions_taken", []), "No decisions recorded.")

        st.markdown("**Open Questions**")
        _render_bullet_list(data.get("open_questions", []), "No open questions recorded.")

    # Tab 2: Action Items
    with tabs[1]:
        action_items = data.get("action_items", [])
        if not action_items:
            st.caption("No action items identified.")
        else:
            for idx, item in enumerate(action_items, start=1):
                with st.container(border=True):
                    st.markdown(f"**{idx}. {item.get('task', 'Untitled task')}**")
                    meta_cols = st.columns(4)
                    with meta_cols[0]:
                        st.caption(f"Owner: {item.get('owner') or 'Not specified'}")
                    with meta_cols[1]:
                        st.caption(f"Team: {item.get('team') or 'Not specified'}")
                    with meta_cols[2]:
                        st.caption(f"Deadline: {item.get('deadline') or 'Not specified'}")
                    with meta_cols[3]:
                        priority = item.get("priority", "Medium")
                        st.caption(f"{PRIORITY_ICONS.get(priority, '⚪')} {priority}")

    # Tab 3: Risks & Blockers
    with tabs[2]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Risks**")
            _render_bullet_list(data.get("risks", []), "No risks identified.")
            st.markdown("**Blockers**")
            _render_bullet_list(data.get("blockers", []), "No blockers identified.")
        with col2:
            st.markdown("**Opportunities**")
            _render_bullet_list(data.get("opportunities", []), "No opportunities identified.")
            st.markdown("**Escalations**")
            _render_bullet_list(data.get("escalations", []), "No escalations identified.")

        st.markdown("**Compliance Issues**")
        _render_bullet_list(data.get("compliance_issues", []), "No compliance issues identified.")

    # Tab 4: Insights
    with tabs[3]:
        st.markdown("**Key Business Insights**")
        _render_bullet_list(data.get("key_business_insights", []), "No key insights identified.")

        st.markdown("**Suggested Next Steps**")
        _render_bullet_list(data.get("suggested_next_steps", []), "No next steps identified.")

        st.markdown("**Next Meeting Agenda**")
        _render_bullet_list(data.get("next_meeting_agenda", []), "No agenda items suggested.")

    # Tab 5: Business Signals
    with tabs[4]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**KPI Mentions**")
            _render_bullet_list(data.get("kpi_mentions", []), "No KPIs mentioned.")
            st.markdown("**Budget Mentions**")
            _render_bullet_list(data.get("budget_mentions", []), "No budget figures mentioned.")
        with col2:
            st.markdown("**Timeline Mentions**")
            _render_bullet_list(data.get("timeline_mentions", []), "No timelines mentioned.")

    # Tab 6: Follow-Up Email
    with tabs[5]:
        email = data.get("follow_up_email", {})
        subject = email.get("subject") or "Not available"
        body = email.get("body") or "Not available"

        st.markdown("**Subject**")
        st.code(subject, language=None)

        st.markdown("**Body**")
        st.text_area(
            label="Follow-up email body",
            value=body,
            height=250,
            label_visibility="collapsed",
        )