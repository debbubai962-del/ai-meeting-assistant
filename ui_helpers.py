"""
components/ui_helpers.py

Shared UI helpers: theme CSS loading, branded header, progress stepper,
section headers, and sidebar status widgets. Keeping these here (not
duplicated in app.py) keeps app.py focused on page composition, not
styling details.
"""

import streamlit as st

from config.settings import ASSETS_DIR, APP_NAME, APP_VERSION


def load_css(filename: str = "style.css") -> None:
    """Loads a CSS file from the assets folder and injects it into the page."""
    css_path = ASSETS_DIR / filename
    if not css_path.exists():
        return
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_header() -> None:
    """Renders a branded gradient header banner at the top of the main area."""
    st.markdown(
        f"""
        <div class="enterprise-header">
            <div class="enterprise-header-title">🗂️ {APP_NAME}</div>
            <div class="enterprise-header-subtitle">
                Turn raw meeting transcripts into executive-ready business reports
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


PIPELINE_STEPS = [
    "Setup",
    "Transcript Input",
    "Cleaning & Validation",
    "Metadata",
    "AI Analysis",
    "Report & Export",
]


def render_progress_stepper(current_step_index: int) -> None:
    """
    Renders a horizontal step progress indicator plus a slim progress bar.

    Args:
        current_step_index: zero-based index of the step currently active
                             in PIPELINE_STEPS.
    """
    badges_html = []
    for index, step_name in enumerate(PIPELINE_STEPS):
        if index < current_step_index:
            css_class = "step-badge done"
            icon = "✓"
        elif index == current_step_index:
            css_class = "step-badge active"
            icon = str(index + 1)
        else:
            css_class = "step-badge pending"
            icon = str(index + 1)

        badges_html.append(
            f'<div class="{css_class}">'
            f'<span class="step-badge-icon">{icon}</span>'
            f'<span class="step-badge-label">{step_name}</span>'
            f'</div>'
        )

    connector = '<div class="step-connector"></div>'
    stepper_html = connector.join(badges_html)

    total_steps = len(PIPELINE_STEPS)
    progress_pct = int(((current_step_index + 1) / total_steps) * 100)

    st.markdown(
        f"""
        <div class="step-stepper">{stepper_html}</div>
        <div class="pipeline-progress-track">
            <div class="pipeline-progress-fill" style="width: {progress_pct}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(icon: str, title: str, description: str = "") -> None:
    """
    Renders a consistent icon + title + description header, used at the
    top of each card/section throughout the app.
    """
    desc_html = f'<div class="section-header-desc">{description}</div>' if description else ""
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-header-icon">{icon}</div>
            <div>
                <div class="section-header-title">{title}</div>
                {desc_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_stats(transcript_text: str | None) -> None:
    """
    Renders a live-updating 'Quick Stats' card in the sidebar reflecting
    the current session state.
    """
    st.markdown("**Quick Stats**")

    if transcript_text:
        char_count = f"{len(transcript_text):,}"
        word_count = f"{len(transcript_text.split()):,}"
        status = "Loaded"
    else:
        char_count = "—"
        word_count = "—"
        status = "Not yet provided"

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="sidebar-stat-row">
                <span class="sidebar-stat-label">Transcript</span>
                <span class="sidebar-stat-value">{status}</span>
            </div>
            <div class="sidebar-stat-row">
                <span class="sidebar-stat-label">Characters</span>
                <span class="sidebar-stat-value">{char_count}</span>
            </div>
            <div class="sidebar-stat-row">
                <span class="sidebar-stat-label">Words</span>
                <span class="sidebar-stat-value">{word_count}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_footer() -> None:
    """Renders a small footer caption at the bottom of the sidebar."""
    st.caption(f"© {APP_NAME} · v{APP_VERSION} · Internal Build")