"""Detect which gitkey profile is active globally or in the current repo."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


def _resolve_path(path: str) -> str:
    return os.path.realpath(os.path.expanduser(path))


def find_git_root(path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", path, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return _resolve_path(result.stdout.strip())


def _git_config_local(repo_root: str, key: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo_root, "config", "--local", key],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _read_lock(lock_path: str) -> str | None:
    if os.path.exists(lock_path):
        with open(lock_path, "r") as f:
            name = f.read().strip()
            return name or None
    return None


def _profile_from_ssh_command(ssh_command: str, path_ssh: str, profiles: dict) -> str | None:
    match = re.search(r'-i\s+"?([^"\s]+)"?', ssh_command)
    if not match:
        return None
    key_path = _resolve_path(match.group(1))
    for name, profile in profiles.items():
        folder = profile.get("folder", "")
        expected = _resolve_path(os.path.join(path_ssh, folder, "id_ed25519"))
        if key_path == expected:
            return name
    return None


def detect_global_profile(
    path_ssh: str,
    profiles: dict,
    key_name: str,
    lock_path: str,
) -> str | None:
    """Profile whose key is currently at ~/.ssh/id_ed25519, else last lock."""
    active_priv = os.path.join(path_ssh, key_name)
    if os.path.exists(active_priv):
        try:
            with open(active_priv, "rb") as f:
                active_bytes = f.read()
            for name, profile in profiles.items():
                folder = profile.get("folder")
                if not folder:
                    continue
                candidate = os.path.join(path_ssh, folder, key_name)
                if os.path.exists(candidate):
                    with open(candidate, "rb") as f:
                        if f.read() == active_bytes:
                            return name
        except OSError:
            pass

    lock_name = _read_lock(lock_path)
    if lock_name and lock_name in profiles:
        return lock_name
    return None


def detect_repo_profile(
    profiles: dict,
    path_ssh: str,
    install_dir: str,
    bindings_file: str,
    cwd: str | None = None,
) -> tuple[str | None, str | None]:
    """Return (profile_name, repo_root) for the current directory, if inside a Git repo."""
    cwd = cwd or os.getcwd()
    repo_root = find_git_root(cwd)
    if not repo_root:
        return None, None

    profile = _git_config_local(repo_root, "gitkey.profile")
    if profile and profile in profiles:
        return profile, repo_root

    if os.path.exists(bindings_file):
        try:
            with open(bindings_file, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for raw_path, bound in data.items():
                    if _resolve_path(raw_path) == repo_root and bound in profiles:
                        return bound, repo_root
        except (json.JSONDecodeError, OSError):
            pass

    ssh_cmd = _git_config_local(repo_root, "core.sshCommand")
    if ssh_cmd:
        inferred = _profile_from_ssh_command(ssh_cmd, path_ssh, profiles)
        if inferred:
            return inferred, repo_root

    return None, repo_root


def get_active_context(
    path_ssh: str,
    install_dir: str,
    profiles: dict,
    key_name: str,
    lock_path: str,
    bindings_file: str,
    cwd: str | None = None,
) -> dict:
    global_profile = detect_global_profile(path_ssh, profiles, key_name, lock_path)
    repo_profile, repo_root = detect_repo_profile(
        profiles, path_ssh, install_dir, bindings_file, cwd
    )
    return {
        "global": global_profile,
        "repo_profile": repo_profile,
        "repo_root": repo_root,
    }
