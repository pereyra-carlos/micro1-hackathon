"""Claude API client shared by the baseline and the agent.

Model and credentials come from the environment: ANTHROPIC_MODEL (default
claude-sonnet-5) and ANTHROPIC_API_KEY. A repo-root .env file is loaded as a
convenience; values already exported win.

Note: current-generation models reject sampling parameters (temperature and
friends return HTTP 400), so determinism is approximated by the structured
answer schema and repeated runs rather than a temperature setting.
"""

import os
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent

MAX_TOKENS = 16000


def _load_dotenv():
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


def client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def usage_dict(response) -> dict:
    usage = response.usage
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }


def add_usage(total: dict, part: dict) -> dict:
    return {key: total.get(key, 0) + part.get(key, 0) for key in set(total) | set(part)}
