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

----------------------------------------------
 📌 ABOUT THE LOCK FILE
----------------------------------------------

The active profile name is stored in:
    ~/.ssh/active_profile.lock

This is used by auto-rotation mode.

==============================================
"""

import os
import sys
import subprocess
from shutil import copyfile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

# Determine SSH directory: if script is in a subfolder, use parent directory (~/.ssh/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Check if script is in a subfolder (e.g., ~/.ssh/switch_profile_git/)
# If settings.py exists in script dir but not in parent, we're in a subfolder
SCRIPT_HAS_SETTINGS = os.path.exists(os.path.join(SCRIPT_DIR, "settings.py")) or os.path.exists(os.path.join(SCRIPT_DIR, "settings-example.py"))
PARENT_HAS_SETTINGS = os.path.exists(os.path.join(PARENT_DIR, "settings.py")) or os.path.exists(os.path.join(PARENT_DIR, "settings-example.py"))

if SCRIPT_HAS_SETTINGS and not PARENT_HAS_SETTINGS:
    # Script is in a subfolder, use parent as PATH_SSH (~/.ssh/)
    PATH_SSH = PARENT_DIR
    SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.py")  # settings.py stays with script
else:
    # Script is at root level (~/.ssh/)
    PATH_SSH = SCRIPT_DIR
    SETTINGS_FILE = os.path.join(PATH_SSH, "settings.py")

LOCK_FILENAME = os.path.join(PATH_SSH, "active_profile.lock")
ALLOWED_SIGNERS_FILE = os.path.join(PATH_SSH, "allowed_signers")
KEY_NAME = "id_ed25519"

# Import PROFILES and GIT_GLOBAL_SCOPE from settings.py
# Add script directory to path so we can import settings.py
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from settings import PROFILES, GIT_GLOBAL_SCOPE
except ImportError:
    example_file = os.path.join(SCRIPT_DIR, "settings-example.py")
    sys.exit(
        f"\nERROR: settings.py not found.\n"
        f"Please copy {example_file} to {SETTINGS_FILE} and configure your settings.\n"
        f"Example: cp {example_file} {SETTINGS_FILE}\n"
    )
except Exception as e:
    sys.exit(f"\nERROR: Failed to load settings.py: {e}\n")


def read_lock():
    """Read last active profile from lock file, if any."""
    if os.path.exists(LOCK_FILENAME):
        with open(LOCK_FILENAME, "r") as f:
            return f.read().strip() or None
    return None


def write_lock(profile_name: str):
    """Persist active profile name to lock file."""
    with open(LOCK_FILENAME, "w") as f:
        f.write(profile_name)


def get_next_profile_name(current: str | None) -> str:
    """Return next profile alphabetically (for auto-rotate mode)."""
    names = sorted(PROFILES.keys())
    if current not in names:
        return names[0]
    idx = names.index(current)
    return names[(idx + 1) % len(names)]


def ask_profile_interactively() -> str:
    """Prompt the user to choose a profile by number or name."""
    if not PROFILES:
        sys.exit("\nERROR: No profiles defined in PROFILES.\n")

    names = sorted(PROFILES.keys())

    print("\nAvailable SSH profiles:")
    for idx, name in enumerate(names, start=1):
        folder = PROFILES[name].get("folder", "-")
        print(f"  {idx}) {name}  (folder: {folder})")

    while True:
        choice = input("\nSelect profile by number or name: ").strip()
        if not choice:
            print("Please enter a value.")
            continue

        # If number was typed
        if choice.isdigit():
            i = int(choice)
            if 1 <= i <= len(names):
                selected = names[i - 1]
                print(f"→ Selected profile: {selected}")
                return selected

        # Try by exact name
        if choice in PROFILES:
            print(f"→ Selected profile: {choice}")
            return choice

        print("Invalid selection, please try again.")


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


def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-p",
        "--profile",
        help=(
            "Profile name (defined in PROFILES) or 'auto' to "
            "rotate between profiles. If omitted, an interactive "
            "selection menu will be shown."
        ),
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Do not modify Git user.name/user.email.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the author of the last commit to match the current profile.",
    )
    args = parser.parse_args()
    
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
    if args.profile is None:
        # Interactive mode
        profile_name = ask_profile_interactively()
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

    # Save selection to lock file (used by auto mode)
    write_lock(profile_name)

    # Apply SSH key and Git config
    copy_keys(profile_name)

    if not args.no_git:
        configure_git(profile_name)


if __name__ == "__main__":
    main()