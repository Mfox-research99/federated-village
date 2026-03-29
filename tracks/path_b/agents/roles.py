"""
tracks/path_b/agents/roles.py — Role registry and config loading

Config resolution order (highest to lowest priority):
  1. CLI flag (--humanist <model>, etc.)
  2. roles.<role> entry in YAML
  3. default_model in YAML
  4. Error: no model specified for role

Prompt files are loaded from federated_village/prompts/ by default.
Override with VILLAGE_PROMPTS_PATH env var (for standalone use without parent repo).
"""

import os
from pathlib import Path
from typing import Any

import yaml

# Path to the parent repo's prompts/ directory
_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"

ROLES = [
    "verification_warden",
    "humanist",
    "witness",
    "analyst",
    "ethicist",
    "pragmatist",
    "witness_proxy",
    "supervisor",
]

# Maps role name → prompt filename in prompts/
ROLE_PROMPT_FILES = {
    "verification_warden": "The_Verification_Warden.md",
    "humanist":            "The_Humanist.md",
    "witness":             "The_Witness.md",
    "analyst":             "The_Analyst.md",
    "ethicist":            "The_Ethicist.md",
    "pragmatist":          "The_Pragmatist.md",
    "witness_proxy":       "The_Witness_Proxy.md",
    "supervisor":          "The_Supervisor.md",
}

SOUL_FILE = "Soul.md"


def prompts_dir() -> Path:
    override = os.environ.get("VILLAGE_PROMPTS_PATH", "")
    return Path(override) if override else _DEFAULT_PROMPTS_DIR


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate a YAML config file. Returns resolved role→model mapping."""
    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    default_model = raw.get("default_model", None)
    role_overrides = raw.get("roles", {}) or {}

    resolved: dict[str, str] = {}
    missing: list[str] = []

    for role in ROLES:
        model = role_overrides.get(role) or default_model
        if not model:
            missing.append(role)
        else:
            resolved[role] = model

    if missing:
        raise ValueError(
            f"Config '{config_path}' specifies no model for role(s): {', '.join(missing)}. "
            "Add a default_model or an explicit entry under roles:"
        )

    return resolved


def apply_cli_overrides(
    resolved: dict[str, str], overrides: dict[str, str | None]
) -> dict[str, str]:
    """Merge CLI flag overrides (highest priority) into the resolved config."""
    result = dict(resolved)
    for role, model in overrides.items():
        if model:
            result[role] = model
    return result


def load_soul(prompts: Path | None = None) -> str:
    d = prompts or prompts_dir()
    path = d / SOUL_FILE
    if not path.exists():
        raise FileNotFoundError(f"Soul.md not found at {path}")
    return path.read_text(encoding="utf-8").strip()


def load_role_prompt(role: str, prompts: Path | None = None) -> str:
    d = prompts or prompts_dir()
    filename = ROLE_PROMPT_FILES.get(role)
    if not filename:
        raise ValueError(f"Unknown role: {role}")
    path = d / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found for role '{role}': {path}")
    return path.read_text(encoding="utf-8").strip()


def build_system_prompt(soul: str, role_prompt: str) -> str:
    return f"{soul}\n\n---\n\n{role_prompt}"
