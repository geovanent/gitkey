"""Read/write ~/.ssh/gitkey/settings.py"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def format_profiles(profiles: dict) -> str:
    lines = ["PROFILES = {"]
    for name in sorted(profiles.keys()):
        p = profiles[name]
        lines.append(f'    "{_escape(name)}": {{')
        lines.append(f'        "folder": "{_escape(p["folder"])}",')
        lines.append(f'        "git_name": "{_escape(p["git_name"])}",')
        lines.append(f'        "git_email": "{_escape(p["git_email"])}",')
        if p.get("sign_commits"):
            lines.append('        "sign_commits": True,')
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


def read_git_global_scope(path: Path, default: bool = True) -> bool:
    if not path.exists():
        return default
    text = path.read_text()
    m = re.search(r"^GIT_GLOBAL_SCOPE\s*=\s*(True|False)", text, re.MULTILINE)
    return m.group(1) == "True" if m else default


def write_settings(path: Path, profiles: dict, git_global_scope: bool) -> None:
    header = """# gitkey settings — edit here or run: gitkey --config

# True = Git identity global; False = only inside current repo
"""
    body = (
        header
        + f"GIT_GLOBAL_SCOPE = {git_global_scope}\n\n"
        + format_profiles(profiles)
        + "\n"
    )
    path.write_text(body)


def reload_settings_module(script_dir: str):
    """Reload settings.py after disk write."""
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    import settings

    importlib.reload(settings)
    return settings.PROFILES, settings.GIT_GLOBAL_SCOPE
