"""Interactive profile creation and configuration menus."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from settings_io import write_settings
from terminal_ui import (
    accent,
    choice_prompt,
    key_cell,
    menu_key,
    muted,
    print_header,
    print_menu_line,
    print_msg_error,
    print_msg_success,
    print_msg_warn,
    print_rule,
    profile_name,
    sign_cell,
    table_header,
)


# ── UI helpers ─────────────────────────────────────────────────────────────

def _prompt(msg: str, default: str = "") -> str:
    if default:
        value = input(f"  {accent(msg)} [{muted(default)}]: ").strip()
        return value or default
    return input(f"  {accent(msg)}: ").strip()


def _prompt_yes_no(msg: str, default: bool = False) -> bool:
    hint = muted("Y/n" if default else "y/N")
    while True:
        ans = input(f"  {msg} ({hint}): ").strip().lower()
        if not ans:
            return default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print_msg_warn("Enter y or n.")


def _header(trail: str) -> None:
    print_header(trail)


def _choice(prompt: str = "Choice") -> str:
    return input(choice_prompt(prompt)).strip().lower()


def _invalid(msg: str) -> None:
    print_msg_warn(msg)


def _term_width(default: int = 72) -> int:
    try:
        return max(60, min(100, os.get_terminal_size().columns - 2))
    except OSError:
        return default


def _clip(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len < 2:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def _profile_names(profiles: dict) -> list[str]:
    return sorted(profiles.keys())


def _resolve_profile_choice(choice: str, profiles: dict) -> str | None:
    names = _profile_names(profiles)
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(names):
            return names[idx - 1]
    if choice in profiles:
        return choice
    return None


# ── Profile data ───────────────────────────────────────────────────────────

def _valid_profile_name(name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name))


def keys_exist(path_ssh: str, folder: str, key_name: str) -> bool:
    priv = os.path.join(path_ssh, folder, key_name)
    return os.path.exists(priv) and os.path.exists(priv + ".pub")


def save_and_reload(
    settings_path: Path, script_dir: str, profiles: dict, scope: bool
) -> tuple[dict, bool]:
    write_settings(settings_path, profiles, scope)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    import settings_io

    return settings_io.reload_settings_module(script_dir)


def print_profiles_table(path_ssh: str, profiles: dict, key_name: str) -> None:
    """One row per profile — display only, no actions in the footer."""
    width = _term_width()
    col_num, col_name, col_sign, col_key = 3, 12, 4, 3
    email_w = width - col_num - col_name - col_sign - col_key - 8

    print_rule(width)
    print(
        f"  {table_header('#'):>{col_num - 1}}  "
        f"{table_header('PROFILE'):<{col_name}} "
        f"{table_header('SIGN'):<{col_sign}} "
        f"{table_header('KEY'):<{col_key}}  "
        f"{table_header('EMAIL')}"
    )
    print_rule(width)

    for i, name in enumerate(_profile_names(profiles), 1):
        p = profiles[name]
        folder = p.get("folder", "?")
        has_key = keys_exist(path_ssh, folder, key_name)
        sign = sign_cell(bool(p.get("sign_commits")), col_sign)
        key = key_cell(has_key, col_key)
        email = muted(_clip(p.get("git_email", ""), email_w))
        num = menu_key(str(i))
        pname = profile_name(_clip(name, col_name))
        pad = " " * max(0, col_name - len(_clip(name, col_name)))
        print(f"  {num:>{col_num - 1}}  {pname}{pad} {sign} {key}  {email}")
    print_rule(width)


# ── SSH key ────────────────────────────────────────────────────────────────

def generate_ssh_key(path_ssh: str, folder: str, email: str, key_name: str) -> bool:
    dest = os.path.join(path_ssh, folder)
    os.makedirs(dest, exist_ok=True)
    priv = os.path.join(dest, key_name)

    if os.path.exists(priv):
        if not _prompt_yes_no(f"Key already exists in {dest}. Overwrite?", False):
            return keys_exist(path_ssh, folder, key_name)

    use_passphrase = _prompt_yes_no("Use a passphrase on the SSH key?", False)
    cmd = ["ssh-keygen", "-t", "ed25519", "-C", email, "-f", priv]
    if use_passphrase:
        print("  (ssh-keygen will prompt for the passphrase)")
    else:
        cmd.extend(["-N", ""])

    print(f"\n  {muted('Generating key at')} {accent(priv)} ...")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print_msg_error("Failed — is ssh-keygen installed?")
        return False
    try:
        os.chmod(priv, 0o600)
    except OSError:
        pass
    print_msg_success("SSH key created")
    return True


def show_pub_key_hint(path_ssh: str, folder: str, key_name: str) -> None:
    pub = os.path.join(path_ssh, folder, key_name + ".pub")
    if os.path.exists(pub):
        print(f"\n  {muted('Public key:')}\n  {accent(f'cat {pub}')}\n")


# ── Screens ────────────────────────────────────────────────────────────────

def screen_pick_profile(
    path_ssh: str,
    profiles: dict,
    key_name: str,
    *,
    title: str,
    back_label: str = "Back",
) -> str | None:
    """Show table and ask for a profile number. Returns None on back."""
    while True:
        _header(title)
        print_profiles_table(path_ssh, profiles, key_name)
        print_menu_line("0", back_label)
        choice = _choice("Profile number")

        if choice in ("0", "b", "back", "q"):
            return None
        name = _resolve_profile_choice(choice, profiles)
        if name:
            return name
        _invalid("Enter the profile number from the list.")


def screen_edit_profile(
    path_ssh: str,
    settings_path: Path,
    script_dir: str,
    profiles: dict,
    git_global_scope: bool,
    key_name: str,
    profile_name: str,
) -> tuple[dict, bool]:
    profiles = dict(profiles)

    while True:
        p = profiles[profile_name]
        sign_on = bool(p.get("sign_commits"))
        has_key = keys_exist(path_ssh, p.get("folder", ""), key_name)

        _header(f"settings / {profile_name}")
        print(f"  {muted('Name:')}    {p.get('git_name')}")
        print(f"  {muted('Email:')}   {p.get('git_email')}")
        folder_path = f"~/.ssh/{p.get('folder')}/"
        print(f"  {muted('Folder:')}  {accent(folder_path)}")
        print(f"  {muted('SSH key:')} {key_cell(has_key)}")
        print(f"  {muted('Signing:')} {sign_cell(sign_on)}")
        print()
        print_menu_line("1", "Toggle signed commits")
        print_menu_line("2", "Edit Git user.name")
        print_menu_line("3", "Edit Git user.email")
        print_menu_line("4", "Create / regenerate SSH key")
        print_menu_line("0", "Back")
        print()

        choice = _choice()

        if choice == "1":
            p["sign_commits"] = not sign_on
            profiles[profile_name] = p
            profiles, git_global_scope = save_and_reload(
                settings_path, script_dir, profiles, git_global_scope
            )
            if p["sign_commits"]:
                print_msg_success("Signed commits enabled")
            else:
                print_msg_success("Signed commits disabled")

        elif choice == "2":
            p["git_name"] = _prompt("Git user.name", p.get("git_name", ""))
            profiles[profile_name] = p
            profiles, git_global_scope = save_and_reload(
                settings_path, script_dir, profiles, git_global_scope
            )
            print_msg_success("Name saved")

        elif choice == "3":
            p["git_email"] = _prompt("Git user.email", p.get("git_email", ""))
            profiles[profile_name] = p
            profiles, git_global_scope = save_and_reload(
                settings_path, script_dir, profiles, git_global_scope
            )
            print_msg_success("Email saved")

        elif choice == "4":
            folder = p.get("folder", profile_name)
            if generate_ssh_key(path_ssh, folder, p.get("git_email", ""), key_name):
                show_pub_key_hint(path_ssh, folder, key_name)

        elif choice in ("0", "b", "back"):
            break
        else:
            _invalid("Pick 1-4 or 0.")

    return profiles, git_global_scope


def screen_settings(
    path_ssh: str,
    settings_path: Path,
    script_dir: str,
    profiles: dict,
    git_global_scope: bool,
    key_name: str,
    *,
    exit_label: str = "Back to main menu",
) -> tuple[dict, bool]:
    """Pick a profile to edit, or create a new one."""
    while True:
        _header("settings")
        print_profiles_table(path_ssh, profiles, key_name)
        print()
        print_menu_line("0", exit_label)
        print_menu_line("n", "New profile")
        print()
        choice = _choice("Profile number to edit")

        if choice in ("0", "q", "quit"):
            break
        if choice in ("n", "new"):
            profiles, git_global_scope, _ = wizard_new_profile(
                path_ssh, settings_path, script_dir, profiles, git_global_scope, key_name
            )
            continue

        name = _resolve_profile_choice(choice, profiles)
        if name:
            profiles, git_global_scope = screen_edit_profile(
                path_ssh,
                settings_path,
                script_dir,
                profiles,
                git_global_scope,
                key_name,
                name,
            )
            continue

        _invalid("Enter a number from the list, n, or 0.")

    return profiles, git_global_scope


def wizard_new_profile(
    path_ssh: str,
    settings_path: Path,
    script_dir: str,
    profiles: dict,
    git_global_scope: bool,
    key_name: str,
    *,
    activate: bool = True,
) -> tuple[dict, bool, str | None]:
    """Create profile + optional SSH key."""
    _header("new profile")

    while True:
        name = _prompt("Profile name (e.g. clientX)")
        if not name:
            continue
        if not _valid_profile_name(name):
            _invalid("Letters, numbers, _ and - only (start with a letter).")
            continue
        if name in profiles:
            _invalid(f"'{name}' already exists.")
            continue
        break

    folder = _prompt("Folder under ~/.ssh", name)
    git_name = _prompt("Git user.name")
    git_email = _prompt("Git user.email")
    sign = _prompt_yes_no("Enable signed commits for this profile?", False)

    profiles = dict(profiles)
    profiles[name] = {
        "folder": folder,
        "git_name": git_name,
        "git_email": git_email,
    }
    if sign:
        profiles[name]["sign_commits"] = True

    if _prompt_yes_no("Generate SSH key now?", True):
        if not generate_ssh_key(path_ssh, folder, git_email, key_name):
            if not _prompt_yes_no("Save profile without a key?", False):
                return profiles, git_global_scope, None
        else:
            show_pub_key_hint(path_ssh, folder, key_name)

    profiles, git_global_scope = save_and_reload(
        settings_path, script_dir, profiles, git_global_scope
    )
    print_msg_success(f"Profile '{name}' saved")

    if activate:
        return profiles, git_global_scope, name
    return profiles, git_global_scope, None


def screen_main_menu(
    path_ssh: str,
    settings_path: Path,
    script_dir: str,
    profiles: dict,
    git_global_scope: bool,
    key_name: str,
) -> tuple[dict, bool, str | None]:
    """Hub: switch, new, or settings — one action per step."""
    while True:
        _header("main menu")
        count = len(profiles)
        print(f"  {muted(f'{count} profile(s) configured.')}\n")
        print_menu_line("1", "Switch to a profile")
        print_menu_line("2", "New profile + SSH key")
        print_menu_line("3", "Profile settings")
        print_menu_line("0", "Quit")
        print()

        choice = _choice()

        if choice == "1":
            name = screen_pick_profile(
                path_ssh, profiles, key_name, title="switch profile"
            )
            if name:
                print_msg_success(f"Activating {profile_name(name)}")
                return profiles, git_global_scope, name

        elif choice == "2":
            return wizard_new_profile(
                path_ssh,
                settings_path,
                script_dir,
                profiles,
                git_global_scope,
                key_name,
            )

        elif choice == "3":
            profiles, git_global_scope = screen_settings(
                path_ssh,
                settings_path,
                script_dir,
                profiles,
                git_global_scope,
                key_name,
            )

        elif choice in ("0", "q", "quit"):
            return profiles, git_global_scope, None

        else:
            _invalid("Enter 1, 2, 3, or 0.")


# ── Public API (called from switch_profile.py) ─────────────────────────────

def menu_config(
    path_ssh: str,
    settings_path: Path,
    script_dir: str,
    profiles: dict,
    git_global_scope: bool,
    key_name: str,
) -> tuple[dict, bool]:
    """Entry from `gitkey --config`."""
    return screen_settings(
        path_ssh,
        settings_path,
        script_dir,
        profiles,
        git_global_scope,
        key_name,
        exit_label="Exit",
    )


def pick_profile_interactive(
    path_ssh: str,
    settings_path: Path,
    script_dir: str,
    profiles: dict,
    git_global_scope: bool,
    key_name: str,
) -> tuple[dict, bool, str | None]:
    """Entry from `gitkey` with no args."""
    if not profiles:
        print_msg_warn("No profiles yet — let's create the first one.")
        return wizard_new_profile(
            path_ssh, settings_path, script_dir, profiles, git_global_scope, key_name
        )
    return screen_main_menu(
        path_ssh, settings_path, script_dir, profiles, git_global_scope, key_name
    )
