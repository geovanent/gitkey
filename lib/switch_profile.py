"""
==============================================
 SSH MULTI PROFILE MANAGER - USER MANUAL
==============================================

This script allows switching between multiple SSH profiles,
each with its own SSH key and Git identity (user.name & user.email).
It also supports SSH commit signing for profiles that require it.

Ideal for consultants working with many clients/projects.

----------------------------------------------
 📌 EXPECTED FOLDER STRUCTURE (inside ~/.ssh/)
----------------------------------------------

~/.ssh/
    switch_profile.py
    active_profile.lock
    allowed_signers          <-- auto-generated file for SSH commit signing verification
    id_ed25519               <-- active SSH key (overwritten by the script)
    id_ed25519.pub
    personal/
        id_ed25519
        id_ed25519.pub
    santander/
        id_ed25519
        id_ed25519.pub
    toro/
        id_ed25519
        id_ed25519.pub
    clientX/
        id_ed25519
        id_ed25519.pub

----------------------------------------------
 📌 ADDING A NEW CLIENT PROFILE
----------------------------------------------

1) Create a folder for the new client inside ~/.ssh:

    mkdir ~/.ssh/clientX

2) Add the key pair inside it:
    ~/.ssh/clientX/id_ed25519
    ~/.ssh/clientX/id_ed25519.pub

3) Add the profile to the PROFILES dictionary in settings.py:

    "clientX": {
        "folder": "clientX",
        "git_name": "Your Name (Client X)",
        "git_email": "your.email@clientx.com",
        "sign_commits": False  # Optional: set to True to enable SSH commit signing
    }

   Note: If settings.py doesn't exist, copy settings-example.py to settings.py first.
   
   You can configure GIT_GLOBAL_SCOPE at the top of settings.py:
   - True: Sets Git config globally (affects all repos) - default behavior
   - False: Sets Git config only for the current repository (must be inside a Git repo)

----------------------------------------------
 📌 HOW TO USE
----------------------------------------------

🔹 Interactive mode (asks which client to use):
    python switch_profile.py

🔹 Activate a specific profile by name:
    python switch_profile.py -p santander
    python switch_profile.py -p personal
    python switch_profile.py -p toro

🔹 Rotate automatically between profiles (alphabetical):
    python switch_profile.py -p auto

🔹 Switch only SSH key (skip Git identity):
    python switch_profile.py --no-git
    python switch_profile.py -p santander --no-git

🔹 Reset last commit author to match current profile:
    python switch_profile.py --reset
    python switch_profile.py --reset -p santander

🔹 Fix last commit (reopen for editing and recommit with current profile):
    python switch_profile.py --fix
    python switch_profile.py -f -p santander

🔹 Bind a profile to a Git repository (per-repo SSH key, no global switch):
    python switch_profile.py --bind -p santander
    python switch_profile.py --bind -p personal /path/to/repo
    python switch_profile.py --bind -p client1 --recursive ~/work/client1

🔹 List or remove repository bindings:
    python switch_profile.py --binds
    python switch_profile.py --unbind
    python switch_profile.py --unbind /path/to/repo

----------------------------------------------
 📌 ABOUT THE LOCK FILE
----------------------------------------------

The active profile name is stored in:
    ~/.ssh/active_profile.lock

This is used by auto-rotation mode.

==============================================
"""

from __future__ import annotations
import json
import os
import sys
import subprocess
from pathlib import Path
from shutil import copyfile
from argparse import ArgumentParser, RawDescriptionHelpFormatter

# Paths: lib/ = code, install root = settings + bindings, ~/.ssh/ = keys + lock
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(LIB_DIR) == "lib":
    INSTALL_DIR = os.path.dirname(LIB_DIR)
    PATH_SSH = os.path.dirname(INSTALL_DIR)
else:
    # Legacy flat layout (~/.ssh/gitkey/switch_profile.py)
    INSTALL_DIR = LIB_DIR
    PATH_SSH = (
        os.path.dirname(INSTALL_DIR)
        if os.path.basename(INSTALL_DIR) == "gitkey"
        else INSTALL_DIR
    )

SETTINGS_FILE = os.path.join(INSTALL_DIR, "settings.py")
SETTINGS_EXAMPLE = os.path.join(LIB_DIR, "settings-example.py")
LOCK_FILENAME = os.path.join(INSTALL_DIR, "active_profile.lock")
LOCK_FILENAME_LEGACY = os.path.join(PATH_SSH, "active_profile.lock")
BINDINGS_FILE = os.path.join(INSTALL_DIR, "repo_bindings.json")
ALLOWED_SIGNERS_FILE = os.path.join(PATH_SSH, "allowed_signers")
KEY_NAME = "id_ed25519"
GITKEY_PROFILE_KEY = "gitkey.profile"
SKIP_WALK_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__"}

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)
if INSTALL_DIR not in sys.path:
    sys.path.insert(0, INSTALL_DIR)

try:
    from settings import PROFILES, GIT_GLOBAL_SCOPE
except ImportError:
    if not os.path.exists(SETTINGS_FILE) and not any(
        f in sys.argv for f in ("--new", "--config")
    ):
        sys.exit(
            f"\nERROR: settings.py not found.\n"
            f"Please copy {SETTINGS_EXAMPLE} to {SETTINGS_FILE}\n"
            f"Or run: gitkey --new\n"
        )
    PROFILES = {}
    GIT_GLOBAL_SCOPE = True
except Exception as e:
    sys.exit(f"\nERROR: Failed to load settings.py: {e}\n")

from profile_wizard import (
    menu_config,
    pick_profile_interactive,
    screen_apply_scope,
    wizard_new_profile,
)


def read_lock():
    """Read last active profile from lock file, if any."""
    for path in (LOCK_FILENAME, LOCK_FILENAME_LEGACY):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as f:
                value = f.read().strip()
                if value:
                    return value
        except OSError:
            continue
    return None


def write_lock(profile_name: str):
    """Persist active profile name to lock file (under install dir, user-writable)."""
    try:
        with open(LOCK_FILENAME, "w") as f:
            f.write(profile_name)
    except PermissionError:
        sys.exit(
            f"\nERROR: Cannot write {LOCK_FILENAME}\n"
            f"Fix permissions: chmod u+w {INSTALL_DIR}\n"
        )
    except OSError as e:
        sys.exit(f"\nERROR: Cannot write lock file: {e}\n")


def get_next_profile_name(current: str | None) -> str:
    """Return next profile alphabetically (for auto-rotate mode)."""
    names = sorted(PROFILES.keys())
    if current not in names:
        return names[0]
    idx = names.index(current)
    return names[(idx + 1) % len(names)]


def reload_profiles_config():
    global PROFILES, GIT_GLOBAL_SCOPE
    from settings_io import reload_settings_module

    PROFILES, GIT_GLOBAL_SCOPE = reload_settings_module(INSTALL_DIR)


def interactive_pick_profile() -> tuple[str | None, str | None]:
    """Menu: switch profile, create new client, or open settings.

    Returns (profile_name, apply_mode) where apply_mode is 'global', 'bind', or None.
    """
    global PROFILES, GIT_GLOBAL_SCOPE
    profiles, scope, name, apply_mode = pick_profile_interactive(
        PATH_SSH,
        Path(SETTINGS_FILE),
        INSTALL_DIR,
        dict(PROFILES),
        GIT_GLOBAL_SCOPE,
        KEY_NAME,
    )
    PROFILES = profiles
    GIT_GLOBAL_SCOPE = scope
    return name, apply_mode


def copy_keys(profile_name: str):
    """Copy SSH keys from profile folder to main ~/.ssh."""
    profile = PROFILES.get(profile_name)
    if not profile:
        sys.exit(
            f"\nERROR: Profile '{profile_name}' not found.\n"
            f"Available profiles: {', '.join(sorted(PROFILES.keys()))}\n"
        )

    folder = profile.get("folder")
    if not folder:
        sys.exit(f"\nERROR: Profile '{profile_name}' has no 'folder' defined.\n")

    src_priv = os.path.join(PATH_SSH, folder, KEY_NAME)
    src_pub = src_priv + ".pub"

    dst_priv = os.path.join(PATH_SSH, KEY_NAME)
    dst_pub = dst_priv + ".pub"

    if not os.path.exists(src_priv) or not os.path.exists(src_pub):
        sys.exit(
            f"\nERROR: SSH keys not found for profile '{profile_name}'.\n"
            f"Expected:\n  {src_priv}\n  {src_pub}\n"
        )

    copyfile(src_priv, dst_priv)
    copyfile(src_pub, dst_pub)

    try:
        os.chmod(dst_priv, 0o600)
    except PermissionError:
        print("WARNING: Could not apply chmod 600 to private key.")

    print(f"\n✅ Active SSH profile: {profile_name} (folder: {folder})")


def update_allowed_signers(profile_name: str):
    """Update the allowed_signers file with the current profile's SSH key and email."""
    profile = PROFILES.get(profile_name, {})
    git_email = profile.get("git_email")
    pub_key_path = os.path.join(PATH_SSH, KEY_NAME + ".pub")

    if not git_email or not os.path.exists(pub_key_path):
        return False

    # Check if file exists and has wrong ownership/permissions
    if os.path.exists(ALLOWED_SIGNERS_FILE):
        try:
            stat_info = os.stat(ALLOWED_SIGNERS_FILE)
            current_uid = os.getuid()
            if stat_info.st_uid != current_uid:
                print(
                    f"⚠️  WARNING: allowed_signers file is owned by another user (UID: {stat_info.st_uid}).\n"
                    f"   Please run: sudo chown $USER {ALLOWED_SIGNERS_FILE}\n"
                    f"   Then run this script again."
                )
                return False
        except OSError:
            pass

    try:
        # Read the public key
        with open(pub_key_path, "r") as f:
            pub_key_content = f.read().strip()

        # Parse the key (format: "ssh-ed25519 AAAA... comment" or "ssh-ed25519 AAAA...")
        parts = pub_key_content.split()
        if len(parts) < 2:
            print(f"⚠️  WARNING: Invalid SSH public key format in {pub_key_path}")
            return False

        key_type = parts[0]  # e.g., "ssh-ed25519"
        key_data = parts[1]  # The actual key data

        # Write to allowed_signers file
        # Format: email key-type key-data [comment]
        signer_line = f"{git_email} {key_type} {key_data}\n"

        # Read existing content to avoid duplicates
        existing_lines = []
        if os.path.exists(ALLOWED_SIGNERS_FILE):
            # Ensure file has correct permissions before reading
            try:
                os.chmod(ALLOWED_SIGNERS_FILE, 0o644)
            except (PermissionError, OSError):
                pass  # Try anyway, might work
            
            try:
                with open(ALLOWED_SIGNERS_FILE, "r") as f:
                    existing_lines = f.readlines()
            except PermissionError:
                # If still can't read, try to fix permissions with chmod command
                subprocess.run(
                    ["chmod", "644", ALLOWED_SIGNERS_FILE],
                    check=False,
                    stderr=subprocess.DEVNULL,
                )
                # Try reading again
                try:
                    with open(ALLOWED_SIGNERS_FILE, "r") as f:
                        existing_lines = f.readlines()
                except Exception as e:
                    print(f"⚠️  WARNING: Could not read existing allowed_signers file: {e}")
                    existing_lines = []

        # Remove any existing line for this email
        existing_lines = [
            line for line in existing_lines if not line.startswith(f"{git_email} ")
        ]

        # Add the new signer line
        existing_lines.append(signer_line)

        # Write back to file
        with open(ALLOWED_SIGNERS_FILE, "w") as f:
            f.writelines(existing_lines)

        # Set proper permissions (readable and writable by owner, readable by group/others)
        # Git needs to read this file, so 0o644 is appropriate
        try:
            os.chmod(ALLOWED_SIGNERS_FILE, 0o644)
        except (PermissionError, OSError) as e:
            print(f"⚠️  WARNING: Could not set permissions on allowed_signers file: {e}")
            # Try to fix permissions using chmod command as fallback
            try:
                subprocess.run(
                    ["chmod", "644", ALLOWED_SIGNERS_FILE],
                    check=False,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

        return True
    except Exception as e:
        print(f"⚠️  WARNING: Failed to update allowed_signers file: {e}")
        return False


def is_git_repo() -> bool:
    """Check if current directory is a Git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def git_config_set(scope: str, key: str, value: str) -> tuple[bool, str]:
    """Set a Git config value with the specified scope (global or local)."""
    if scope == "local" and not is_git_repo():
        return False, "Not in a Git repository"
    
    scope_flag = "--global" if scope == "global" else "--local"
    result = subprocess.run(
        ["git", "config", scope_flag, key, value],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    return False, result.stderr.decode().strip()


def git_config_get(scope: str, key: str) -> str:
    """Get a Git config value with the specified scope (global or local)."""
    if scope == "local" and not is_git_repo():
        return ""
    
    scope_flag = "--global" if scope == "global" else "--local"
    result = subprocess.run(
        ["git", "config", scope_flag, key],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def git_config_unset(scope: str, key: str) -> bool:
    """Unset a Git config value with the specified scope (global or local)."""
    if scope == "local" and not is_git_repo():
        return False
    
    scope_flag = "--global" if scope == "global" else "--local"
    result = subprocess.run(
        ["git", "config", scope_flag, "--unset", key],
        check=False,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def configure_git(profile_name: str):
    """Configure Git identity (user.name & user.email) and commit signing with configurable scope."""
    profile = PROFILES.get(profile_name, {})
    git_name = profile.get("git_name")
    git_email = profile.get("git_email")
    sign_commits = profile.get("sign_commits", False)
    
    # Convert GIT_GLOBAL_SCOPE boolean to scope string
    git_scope = "global" if GIT_GLOBAL_SCOPE else "local"

    if not git_name and not git_email and not sign_commits:
        return

    scope_label = "globally" if git_scope == "global" else "locally (current repo)"

    # Configure user.name and user.email
    if git_name or git_email:
        # Show current configuration before updating
        current_name = git_config_get(git_scope, "user.name")
        current_email = git_config_get(git_scope, "user.email")
        
        if current_name or current_email:
            print(f"   Current {git_scope} Git config: {current_name or '(not set)'} <{current_email or '(not set)'}>")

        # Configure user.name
        if git_name:
            success, error = git_config_set(git_scope, "user.name", git_name)
            if success:
                print(f"   ✓ Git user.name set {scope_label} to: {git_name}")
            else:
                if git_scope == "local" and "Not in a Git repository" in error:
                    print(f"   ⚠️  Cannot set Git user.name locally: {error}")
                else:
                    print(f"   ⚠️  Failed to set Git user.name: {error}")
        
        # Configure user.email
        if git_email:
            success, error = git_config_set(git_scope, "user.email", git_email)
            if success:
                print(f"   ✓ Git user.email set {scope_label} to: {git_email}")
            else:
                if git_scope == "local" and "Not in a Git repository" in error:
                    print(f"   ⚠️  Cannot set Git user.email locally: {error}")
                else:
                    print(f"   ⚠️  Failed to set Git user.email: {error}")

    # Configure commit signing
    # Note: allowedSignersFile is always set globally as it's a system-wide setting
    if sign_commits:
        pub_key_path = os.path.join(PATH_SSH, KEY_NAME + ".pub")
        if os.path.exists(pub_key_path):
            # Update allowed_signers file (always global)
            if update_allowed_signers(profile_name):
                # Configure Git to use the allowed_signers file (always global)
                subprocess.run(
                    [
                        "git",
                        "config",
                        "--global",
                        "gpg.ssh.allowedSignersFile",
                        ALLOWED_SIGNERS_FILE,
                    ],
                    check=False,
                )

            # Set commit signing config with the specified scope
            git_config_set(git_scope, "commit.gpgsign", "true")
            git_config_set(git_scope, "tag.gpgsign", "true")
            git_config_set(git_scope, "gpg.format", "ssh")
            git_config_set(git_scope, "user.signingkey", pub_key_path)
            print(f"🔐 Commit signing enabled {scope_label} (SSH) for profile: {profile_name}")
        else:
            print(
                f"⚠️  WARNING: SSH public key not found at {pub_key_path}. "
                "Commit signing not configured."
            )
    else:
        # Disable commit signing for profiles that don't require it
        git_config_unset(git_scope, "commit.gpgsign")
        git_config_unset(git_scope, "tag.gpgsign")
        git_config_unset(git_scope, "gpg.format")
        git_config_unset(git_scope, "user.signingkey")
        # Note: We keep gpg.ssh.allowedSignersFile configured globally even when signing is disabled
        # so it's available for verification of existing signed commits

    print(f"🧾 Git identity updated {scope_label} for profile: {profile_name}\n")


def resolve_path(path: str) -> str:
    """Return absolute, normalized path."""
    return os.path.realpath(os.path.expanduser(path))


def get_profile_key_paths(profile_name: str) -> tuple[str, str]:
    """Return (private_key, public_key) paths for a profile."""
    profile = PROFILES.get(profile_name)
    if not profile:
        sys.exit(
            f"\nERROR: Profile '{profile_name}' not found.\n"
            f"Available profiles: {', '.join(sorted(PROFILES.keys()))}\n"
        )
    folder = profile.get("folder")
    if not folder:
        sys.exit(f"\nERROR: Profile '{profile_name}' has no 'folder' defined.\n")
    priv = os.path.join(PATH_SSH, folder, KEY_NAME)
    pub = priv + ".pub"
    if not os.path.exists(priv) or not os.path.exists(pub):
        sys.exit(
            f"\nERROR: SSH keys not found for profile '{profile_name}'.\n"
            f"Expected:\n  {priv}\n  {pub}\n"
        )
    return priv, pub


def build_ssh_command(private_key_path: str) -> str:
    """Git core.sshCommand value that forces a specific identity."""
    return f'ssh -i "{private_key_path}" -o IdentitiesOnly=yes'


def find_git_root(path: str) -> str | None:
    """Return Git repository root for path, or None."""
    result = subprocess.run(
        ["git", "-C", path, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return resolve_path(result.stdout.strip())


def find_git_repos_under(root: str) -> list[str]:
    """Find all Git repository roots under a directory tree."""
    root = resolve_path(root)
    if not os.path.isdir(root):
        sys.exit(f"\nERROR: Not a directory: {root}\n")

    repos: set[str] = set()
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_WALK_DIRS]
        git_root = find_git_root(dirpath)
        if git_root:
            repos.add(git_root)

    return sorted(repos)


def load_bindings() -> dict[str, str]:
    """Load repo path -> profile name bindings."""
    if not os.path.exists(BINDINGS_FILE):
        return {}
    try:
        with open(BINDINGS_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {resolve_path(k): v for k, v in data.items()}
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  WARNING: Could not read {BINDINGS_FILE}: {e}")
        return {}


def save_bindings(bindings: dict[str, str]) -> None:
    """Persist repo bindings to disk."""
    try:
        with open(BINDINGS_FILE, "w") as f:
            json.dump(bindings, f, indent=2, sort_keys=True)
            f.write("\n")
    except OSError as e:
        sys.exit(f"\nERROR: Could not write bindings file: {e}\n")


def git_config_local(repo_root: str, key: str, value: str) -> tuple[bool, str]:
    """Set a local Git config value inside a specific repository."""
    result = subprocess.run(
        ["git", "-C", repo_root, "config", "--local", key, value],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    return False, result.stderr.decode().strip()


def git_config_local_unset(repo_root: str, key: str) -> bool:
    """Unset a local Git config value inside a specific repository."""
    result = subprocess.run(
        ["git", "-C", repo_root, "config", "--local", "--unset", key],
        check=False,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def git_config_local_get(repo_root: str, key: str) -> str:
    """Read a local Git config value from a specific repository."""
    result = subprocess.run(
        ["git", "-C", repo_root, "config", "--local", key],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def add_allowed_signers_entry(git_email: str, pub_key_path: str) -> bool:
    """Add or update one email entry in allowed_signers using a public key file."""
    if not git_email or not os.path.exists(pub_key_path):
        return False

    try:
        with open(pub_key_path, "r") as f:
            pub_key_content = f.read().strip()
        parts = pub_key_content.split()
        if len(parts) < 2:
            return False
        signer_line = f"{git_email} {parts[0]} {parts[1]}\n"

        existing_lines: list[str] = []
        if os.path.exists(ALLOWED_SIGNERS_FILE):
            try:
                os.chmod(ALLOWED_SIGNERS_FILE, 0o644)
                with open(ALLOWED_SIGNERS_FILE, "r") as f:
                    existing_lines = f.readlines()
            except (PermissionError, OSError):
                pass

        existing_lines = [
            line for line in existing_lines if not line.startswith(f"{git_email} ")
        ]
        existing_lines.append(signer_line)

        with open(ALLOWED_SIGNERS_FILE, "w") as f:
            f.writelines(existing_lines)
        try:
            os.chmod(ALLOWED_SIGNERS_FILE, 0o644)
        except (PermissionError, OSError):
            pass
        return True
    except Exception as e:
        print(f"⚠️  WARNING: Failed to update allowed_signers: {e}")
        return False


def configure_repo_binding(repo_root: str, profile_name: str) -> None:
    """Apply per-repository SSH key and Git identity (local config only)."""
    profile = PROFILES.get(profile_name, {})
    priv, pub = get_profile_key_paths(profile_name)
    git_name = profile.get("git_name")
    git_email = profile.get("git_email")
    sign_commits = profile.get("sign_commits", False)

    success, error = git_config_local(
        repo_root, "core.sshCommand", build_ssh_command(priv)
    )
    if not success:
        sys.exit(f"\nERROR: Failed to set core.sshCommand: {error}\n")

    if git_name:
        git_config_local(repo_root, "user.name", git_name)
    if git_email:
        git_config_local(repo_root, "user.email", git_email)

    git_config_local(repo_root, GITKEY_PROFILE_KEY, profile_name)

    if sign_commits:
        add_allowed_signers_entry(git_email, pub)
        subprocess.run(
            [
                "git",
                "config",
                "--global",
                "gpg.ssh.allowedSignersFile",
                ALLOWED_SIGNERS_FILE,
            ],
            check=False,
        )
        git_config_local(repo_root, "commit.gpgsign", "true")
        git_config_local(repo_root, "tag.gpgsign", "true")
        git_config_local(repo_root, "gpg.format", "ssh")
        git_config_local(repo_root, "user.signingkey", pub)
    else:
        for key in ("commit.gpgsign", "tag.gpgsign", "gpg.format", "user.signingkey"):
            git_config_local_unset(repo_root, key)


def clear_repo_binding(repo_root: str) -> None:
    """Remove per-repository binding from Git local config."""
    for key in (
        "core.sshCommand",
        "user.name",
        "user.email",
        GITKEY_PROFILE_KEY,
        "commit.gpgsign",
        "tag.gpgsign",
        "gpg.format",
        "user.signingkey",
    ):
        git_config_local_unset(repo_root, key)


def bind_repository(profile_name: str, path: str, recursive: bool = False) -> None:
    """Bind a profile to one or more Git repositories under path."""
    if profile_name not in PROFILES:
        sys.exit(
            f"\nERROR: Profile '{profile_name}' does not exist.\n"
            f"Profiles: {', '.join(sorted(PROFILES.keys()))}\n"
        )

    get_profile_key_paths(profile_name)
    target = resolve_path(path)

    if recursive:
        repo_roots = find_git_repos_under(target)
        if not repo_roots:
            sys.exit(f"\nERROR: No Git repositories found under: {target}\n")
    else:
        repo_root = find_git_root(target)
        if not repo_root:
            sys.exit(
                f"\nERROR: Not a Git repository: {target}\n"
                f"Run from inside a repo, pass a repo path, or use --recursive.\n"
            )
        repo_roots = [repo_root]

    bindings = load_bindings()
    for repo_root in repo_roots:
        configure_repo_binding(repo_root, profile_name)
        bindings[repo_root] = profile_name
        print(f"🔗 Bound '{profile_name}' → {repo_root}")

    save_bindings(bindings)
    print(
        f"\n✅ {len(repo_roots)} repository(ies) now use profile '{profile_name}' "
        f"(SSH key stays in ~/.ssh/{PROFILES[profile_name]['folder']}/).\n"
        f"   Global default key was not changed.\n"
    )


def unbind_repository(path: str) -> None:
    """Remove profile binding from a Git repository."""
    target = resolve_path(path)
    repo_root = find_git_root(target)
    if not repo_root:
        sys.exit(
            f"\nERROR: Not a Git repository: {target}\n"
        )

    bindings = load_bindings()
    profile_name = bindings.pop(repo_root, None) or git_config_local_get(
        repo_root, GITKEY_PROFILE_KEY
    )

    clear_repo_binding(repo_root)

    if profile_name:
        save_bindings(bindings)
        print(f"\n✅ Removed binding '{profile_name}' from {repo_root}\n")
    else:
        save_bindings(bindings)
        print(f"\n✅ Cleared local Git config in {repo_root} (no binding was recorded)\n")


def list_bindings() -> None:
    """Show all repository bindings."""
    bindings = load_bindings()
    if not bindings:
        print("\nNo repository bindings configured.")
        print("Use: gitkey --bind -p <profile> [path]\n")
        return

    print("\nRepository bindings (per-repo SSH keys):\n")
    for repo_root in sorted(bindings):
        profile_name = bindings[repo_root]
        exists = "✓" if os.path.isdir(repo_root) else "⚠ missing"
        active = git_config_local_get(repo_root, GITKEY_PROFILE_KEY)
        status = ""
        if active and active != profile_name:
            status = f"  (git config: {active})"
        elif not active:
            status = "  (git config not set — run --bind again)"
        folder = PROFILES.get(profile_name, {}).get("folder", "?")
        print(f"  {exists}  {profile_name} ({folder}/)")
        print(f"         {repo_root}{status}")
    print()


def reset_last_commit(profile_name: str):
    """Reset the author of the last commit to match the current profile."""
    if not is_git_repo():
        sys.exit("\nERROR: Not in a Git repository. Cannot reset last commit.\n")
    
    # Check if there are any commits
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0 or not result.stdout.strip() or result.stdout.strip() == "0":
        sys.exit("\nERROR: No commits found. Nothing to reset.\n")
    
    profile = PROFILES.get(profile_name)
    if not profile:
        sys.exit(
            f"\nERROR: Profile '{profile_name}' not found.\n"
            f"Available profiles: {', '.join(sorted(PROFILES.keys()))}\n"
        )
    
    git_name = profile.get("git_name")
    git_email = profile.get("git_email")
    sign_commits = profile.get("sign_commits", False)
    
    if not git_name or not git_email:
        sys.exit(
            f"\nERROR: Profile '{profile_name}' does not have git_name and git_email configured.\n"
        )
    
    # Get current commit info
    result = subprocess.run(
        ["git", "log", "-1", "--format=%an <%ae>", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    current_author = result.stdout.strip() if result.returncode == 0 else "unknown"
    
    print(f"\n📝 Resetting last commit author:")
    print(f"   Current: {current_author}")
    print(f"   New:     {git_name} <{git_email}>")
    
    # Configure Git for signing if needed (before amend, so it re-signs automatically)
    git_scope = "global" if GIT_GLOBAL_SCOPE else "local"
    if sign_commits:
        pub_key_path = os.path.join(PATH_SSH, KEY_NAME + ".pub")
        if os.path.exists(pub_key_path):
            update_allowed_signers(profile_name)
            git_config_set(git_scope, "commit.gpgsign", "true")
            git_config_set(git_scope, "gpg.format", "ssh")
            git_config_set(git_scope, "user.signingkey", pub_key_path)
        else:
            print(f"   ⚠️  Warning: SSH public key not found. Commit will not be signed.")
    
    # Amend the commit with new author (will auto re-sign if commit.gpgsign is true)
    author_string = f"{git_name} <{git_email}>"
    result = subprocess.run(
        ["git", "commit", "--amend", "--author", author_string, "--no-edit"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0:
        sys.exit(
            f"\nERROR: Failed to amend commit.\n"
            f"Error: {result.stderr.strip()}\n"
        )
    
    print(f"   ✓ Commit author updated successfully")
    if sign_commits:
        print(f"   ✓ Commit re-signed with SSH key")
    
    print()


def fix_last_commit(profile_name: str):
    """Fix the last commit by reopening it for editing and recommitting with the current profile."""
    if not is_git_repo():
        sys.exit("\nERROR: Not in a Git repository. Cannot fix last commit.\n")
    
    # Check if there are any commits
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0 or not result.stdout.strip() or result.stdout.strip() == "0":
        sys.exit("\nERROR: No commits found. Nothing to fix.\n")
    
    profile = PROFILES.get(profile_name)
    if not profile:
        sys.exit(
            f"\nERROR: Profile '{profile_name}' not found.\n"
            f"Available profiles: {', '.join(sorted(PROFILES.keys()))}\n"
        )
    
    git_name = profile.get("git_name")
    git_email = profile.get("git_email")
    sign_commits = profile.get("sign_commits", False)
    
    if not git_name or not git_email:
        sys.exit(
            f"\nERROR: Profile '{profile_name}' does not have git_name and git_email configured.\n"
        )
    
    # Get current commit info
    result = subprocess.run(
        ["git", "log", "-1", "--format=%an <%ae>%n%s", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n', 1)
        current_author = lines[0] if len(lines) > 0 else "unknown"
        current_message = lines[1] if len(lines) > 1 else ""
    else:
        current_author = "unknown"
        current_message = ""
    
    print(f"\n🔧 Fixing last commit:")
    print(f"   Current author: {current_author}")
    print(f"   New author:     {git_name} <{git_email}>")
    if current_message:
        print(f"   Current message: {current_message[:50]}{'...' if len(current_message) > 50 else ''}")
    
    # Configure Git identity first
    git_scope = "global" if GIT_GLOBAL_SCOPE else "local"
    git_config_set(git_scope, "user.name", git_name)
    git_config_set(git_scope, "user.email", git_email)
    
    # Configure Git for signing if needed
    if sign_commits:
        pub_key_path = os.path.join(PATH_SSH, KEY_NAME + ".pub")
        if os.path.exists(pub_key_path):
            update_allowed_signers(profile_name)
            git_config_set(git_scope, "commit.gpgsign", "true")
            git_config_set(git_scope, "tag.gpgsign", "true")
            git_config_set(git_scope, "gpg.format", "ssh")
            git_config_set(git_scope, "user.signingkey", pub_key_path)
            print(f"   ✓ Commit signing configured (SSH)")
        else:
            print(f"   ⚠️  Warning: SSH public key not found. Commit will not be signed.")
    else:
        # Disable signing if profile doesn't require it
        git_config_unset(git_scope, "commit.gpgsign")
        git_config_unset(git_scope, "tag.gpgsign")
        git_config_unset(git_scope, "gpg.format")
        git_config_unset(git_scope, "user.signingkey")
    
    print(f"\n   Opening commit editor...")
    print(f"   (You can edit the commit message if needed)")
    
    # Amend the commit (opens editor for message editing)
    # This will use the current Git config (user.name, user.email) and signing settings
    result = subprocess.run(
        ["git", "commit", "--amend"],
        check=False,
    )
    
    if result.returncode != 0:
        sys.exit(
            f"\nERROR: Failed to amend commit.\n"
            f"The commit was not modified.\n"
        )
    
    print(f"\n   ✓ Commit fixed successfully")
    if sign_commits:
        print(f"   ✓ Commit signed with SSH key")
    print()


HELP_EPILOG = """
examples:
  gitkey                         Interactive menu
  gitkey -p personal             Switch global key + Git identity
  gitkey -p auto                 Rotate to next profile (alphabetical)
  gitkey --bind -p clientA       Bind profile to current repo only
  gitkey --bind -p clientA ~/proj Bind profile to a specific repo path
  gitkey --bind -p clientA -r ~/work/client   Bind all repos under a folder
  gitkey --binds                 List repositories bound to profiles
  gitkey --unbind                Remove binding from current repo
  gitkey --new                   Create profile + SSH key (wizard)
  gitkey --config                Settings: signing, email, keys
  gitkey --reset -p personal     Rewrite last commit author
  gitkey -f -p personal          Amend last commit with profile

config:  ~/.ssh/gitkey/settings.py
install: curl -fsSL https://raw.githubusercontent.com/geovanent/gitkey/main/install.sh | bash
"""


def main():
    parser = ArgumentParser(
        prog="gitkey",
        description="Switch SSH keys and Git identities for multiple clients.",
        formatter_class=RawDescriptionHelpFormatter,
        epilog=HELP_EPILOG,
    )

    bind_group = parser.add_argument_group("per-repository (multiple keys at once)")
    bind_group.add_argument(
        "directory",
        nargs="?",
        default=".",
        metavar="PATH",
        help="Repo or folder for --bind / --unbind (default: .)",
    )
    bind_group.add_argument(
        "--bind",
        action="store_true",
        help="Bind profile to PATH (local core.sshCommand; global key unchanged)",
    )
    bind_group.add_argument(
        "--unbind",
        action="store_true",
        help="Remove profile binding from PATH",
    )
    bind_group.add_argument(
        "--binds",
        action="store_true",
        help="List all repository bindings",
    )
    bind_group.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="With --bind, bind every Git repo under PATH",
    )

    profile_group = parser.add_argument_group("switch profile")
    profile_group.add_argument(
        "-p",
        "--profile",
        metavar="NAME",
        help="Profile name, or 'auto' to rotate; omit for interactive menu",
    )
    profile_group.add_argument(
        "--no-git",
        action="store_true",
        help="Change SSH key only; do not set user.name / user.email",
    )

    setup_group = parser.add_argument_group("setup")
    setup_group.add_argument(
        "--new",
        action="store_true",
        help="Create a new profile and SSH key (wizard)",
    )
    setup_group.add_argument(
        "--config",
        action="store_true",
        help="Edit profiles: signed commits, Git identity, SSH keys",
    )

    commit_group = parser.add_argument_group("last commit")
    commit_group.add_argument(
        "--reset",
        action="store_true",
        help="Set last commit author to the profile",
    )
    commit_group.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="Amend last commit (message + author + signing)",
    )

    args = parser.parse_args()

    global PROFILES, GIT_GLOBAL_SCOPE

    if (args.new or args.config) and not os.path.exists(SETTINGS_FILE):
        example = SETTINGS_EXAMPLE
        if os.path.exists(example):
            copyfile(example, SETTINGS_FILE)
            reload_profiles_config()
        else:
            sys.exit(f"\nERROR: {SETTINGS_FILE} not found and no settings-example.py.\n")

    if args.config:
        PROFILES, GIT_GLOBAL_SCOPE = menu_config(
            PATH_SSH,
            Path(SETTINGS_FILE),
            INSTALL_DIR,
            dict(PROFILES),
            GIT_GLOBAL_SCOPE,
            KEY_NAME,
        )
        return

    if args.new:
        PROFILES, GIT_GLOBAL_SCOPE, created = wizard_new_profile(
            PATH_SSH,
            Path(SETTINGS_FILE),
            INSTALL_DIR,
            dict(PROFILES),
            GIT_GLOBAL_SCOPE,
            KEY_NAME,
        )
        if not created:
            return
        if args.profile and args.profile != created:
            print(f"Note: ignoring -p {args.profile}, using new profile '{created}'")
        write_lock(created)
        copy_keys(created)
        if not args.no_git:
            configure_git(created)
        return

    if args.binds:
        list_bindings()
        return

    if args.unbind:
        unbind_repository(args.directory)
        return

    if args.bind:
        if not args.profile:
            sys.exit(
                "\nERROR: --bind requires a profile (-p/--profile).\n"
                "Example: gitkey --bind -p personal\n"
            )
        bind_repository(args.profile, args.directory, recursive=args.recursive)
        return

    # Handle --fix mode
    if args.fix:
        # Determine which profile to use for fix
        if args.profile:
            if args.profile not in PROFILES:
                sys.exit(
                    f"\nERROR: Profile '{args.profile}' does not exist.\n"
                    f"Profiles: {', '.join(sorted(PROFILES.keys()))}\n"
                )
            profile_name = args.profile
        else:
            # Use the active profile from lock file
            profile_name = read_lock()
            if not profile_name or profile_name not in PROFILES:
                sys.exit(
                    "\nERROR: No active profile found.\n"
                    "Please specify a profile with -p/--profile or switch to a profile first.\n"
                )
            print(f"Using active profile: {profile_name}")
        
        # Apply SSH key first (needed for signing)
        copy_keys(profile_name)
        
        # Fix the commit
        fix_last_commit(profile_name)
        return
    
    # Handle --reset mode
    if args.reset:
        # Determine which profile to use for reset
        if args.profile:
            if args.profile not in PROFILES:
                sys.exit(
                    f"\nERROR: Profile '{args.profile}' does not exist.\n"
                    f"Profiles: {', '.join(sorted(PROFILES.keys()))}\n"
                )
            profile_name = args.profile
        else:
            # Use the active profile from lock file
            profile_name = read_lock()
            if not profile_name or profile_name not in PROFILES:
                sys.exit(
                    "\nERROR: No active profile found.\n"
                    "Please specify a profile with -p/--profile or switch to a profile first.\n"
                )
            print(f"Using active profile: {profile_name}")
        
        # Apply SSH key first (needed for signing)
        copy_keys(profile_name)
        
        # Reset the commit
        reset_last_commit(profile_name)
        return

    # Decide which profile to use
    apply_mode = "global"
    if args.profile is None:
        profile_name, apply_mode = interactive_pick_profile()
        if profile_name is None:
            return
        if apply_mode == "bind":
            bind_repository(profile_name, args.directory)
            return
    elif args.profile == "auto":
        # Auto-rotate mode
        current = read_lock()
        profile_name = get_next_profile_name(current)
        print(f"\nAuto-rotate mode. Selected profile: {profile_name}")
    else:
        # Profile passed by argument
        if args.profile not in PROFILES:
            sys.exit(
                f"\nERROR: Profile '{args.profile}' does not exist.\n"
                f"Profiles: {', '.join(sorted(PROFILES.keys()))}\n"
            )
        profile_name = args.profile
        if (
            not args.bind
            and not args.no_git
            and sys.stdin.isatty()
            and sys.stdout.isatty()
        ):
            chosen = screen_apply_scope(profile_name, args.directory)
            if chosen is None:
                return
            if chosen == "bind":
                bind_repository(profile_name, args.directory)
                return
            apply_mode = "global"

    # Save selection to lock file (used by auto mode)
    write_lock(profile_name)

    # Apply SSH key and Git config
    copy_keys(profile_name)

    if not args.no_git:
        configure_git(profile_name)


if __name__ == "__main__":
    main()