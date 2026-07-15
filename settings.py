"""
config/settings.py

Central configuration module for the AI Business Meeting Assistant.

Loads configuration from (in priority order):
    1. Streamlit Cloud secrets (st.secrets) - used only if a secrets.toml
       file actually exists (cloud deployment)
    2. .env file via python-dotenv - used in local development

We only touch st.secrets if a secrets.toml file is actually present on
disk. This avoids Streamlit's "No secrets found" warning from firing
during local development, which would otherwise break the requirement
that st.set_page_config() be the first Streamlit command executed.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False


BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"
PROMPTS_DIR = BASE_DIR / "prompts"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# Only consider st.secrets usable if an actual secrets.toml file exists
# somewhere Streamlit would look for it. This prevents accidentally
# triggering Streamlit's built-in "No secrets found" warning locally.
_PROJECT_SECRETS_FILE = BASE_DIR / ".streamlit" / "secrets.toml"
_HOME_SECRETS_FILE = Path.home() / ".streamlit" / "secrets.toml"
_SECRETS_FILE_EXISTS = _PROJECT_SECRETS_FILE.exists() or _HOME_SECRETS_FILE.exists()


def _get_setting(key: str, default: str = "") -> str:
    """
    Reads a config value from Streamlit secrets first (only if a
    secrets.toml file actually exists - this is true on Streamlit
    Cloud), falling back to environment variables (local .env file).
    """
    if _HAS_STREAMLIT and _SECRETS_FILE_EXISTS:
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    return os.getenv(key, default)


OPENROUTER_API_KEY = _get_setting("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = _get_setting("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = _get_setting("OPENROUTER_MODEL", "openai/gpt-4o-mini")

APP_NAME = "AI Business Meeting Assistant"
APP_VERSION = "0.1.0"


def is_api_key_configured() -> bool:
    """
    Returns True if an OpenRouter API key has been set (via Streamlit
    secrets or .env) and is not the placeholder value.
    """
    if not OPENROUTER_API_KEY:
        return False
    if OPENROUTER_API_KEY.strip() == "your_openrouter_api_key_here":
        return False
    return True