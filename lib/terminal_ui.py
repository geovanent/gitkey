"""ANSI colors for gitkey terminal UI (TTY-aware, respects NO_COLOR)."""

from __future__ import annotations

import os
import re
import sys

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


class _C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"


_enabled: bool | None = None


def colors_enabled() -> bool:
    global _enabled
    if _enabled is not None:
        return _enabled
    if os.environ.get("NO_COLOR") is not None:
        _enabled = False
    elif os.environ.get("FORCE_COLOR") or os.environ.get("CLICOLOR_FORCE"):
        _enabled = True
    elif not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        _enabled = False
    elif os.environ.get("TERM", "") == "dumb":
        _enabled = False
    else:
        _enabled = True
    return _enabled


def visible_len(text: str) -> int:
    return len(_ANSI_RE.sub("", text))


def stylize(text: str, *codes: str) -> str:
    if not colors_enabled():
        return text
    return "".join(codes) + text + _C.RESET


def brand(text: str) -> str:
    return stylize(text, _C.BOLD, _C.CYAN)


def title(text: str) -> str:
    return stylize(text, _C.BOLD)


def muted(text: str) -> str:
    return stylize(text, _C.DIM)


def accent(text: str) -> str:
    return stylize(text, _C.CYAN)


def ok(text: str) -> str:
    return stylize(text, _C.GREEN)


def warn(text: str) -> str:
    return stylize(text, _C.YELLOW)


def err(text: str) -> str:
    return stylize(text, _C.RED)


def menu_key(text: str) -> str:
    return stylize(text, _C.BOLD, _C.YELLOW)


def table_header(text: str) -> str:
    return stylize(text, _C.BOLD, _C.BLUE) if colors_enabled() else text


def sign_cell(on: bool, width: int = 4) -> str:
    raw = "ON" if on else "OFF"
    cell = ok(raw) if on else muted(raw)
    return cell + " " * max(0, width - len(raw))


def key_cell(has_key: bool, width: int = 3) -> str:
    raw = "yes" if has_key else "no"
    cell = ok(raw) if has_key else err(raw)
    return cell + " " * max(0, width - len(raw))


def profile_name(text: str) -> str:
    return stylize(text, _C.BOLD)


def pad_visible(text: str, width: int) -> str:
    """Pad colored text to visible width."""
    pad = width - visible_len(text)
    return text + (" " * pad if pad > 0 else "")


def print_header(trail: str) -> None:
    print()
    print(f"  {brand('gitkey')}  {muted('›')}  {title(trail)}")
    print()


def print_rule(width: int) -> None:
    line = "─" * (width - 2)
    print(f"  {muted(line)}")


def print_menu_line(key: str, label: str) -> None:
    print(f"  {menu_key(key)}  {label}")


def print_msg_success(text: str) -> None:
    print(f"\n  {ok('✓')} {text}\n")


def print_msg_warn(text: str) -> None:
    print(f"\n  {warn('!')} {text}\n")


def print_msg_error(text: str) -> None:
    print(f"\n  {err('✗')} {text}\n")


def choice_prompt(label: str = "Choice") -> str:
    return f"  {accent(label)}: "
