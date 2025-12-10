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
    change_keys.py
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

3) Add the profile to the PROFILES dictionary in this script:

    "clientX": {
        "folder": "clientX",
        "git_name": "Your Name (Client X)",
        "git_email": "your.email@clientx.com",
        "sign_commits": False  # Optional: set to True to enable SSH commit signing
    }

----------------------------------------------
 📌 HOW TO USE
----------------------------------------------

🔹 Interactive mode (asks which client to use):
    python change_keys.py

🔹 Activate a specific profile by name:
    python change_keys.py -p santander
    python change_keys.py -p personal
    python change_keys.py -p toro

🔹 Rotate automatically between profiles (alphabetical):
    python change_keys.py -p auto

🔹 Switch only SSH key (skip Git identity):
    python change_keys.py --no-git
    python change_keys.py -p santander --no-git

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

PATH_SSH = os.path.dirname(__file__)   # typically ~/.ssh
LOCK_FILENAME = os.path.join(PATH_SSH, "active_profile.lock")
ALLOWED_SIGNERS_FILE = os.path.join(PATH_SSH, "allowed_signers")
KEY_NAME = "id_ed25519"


# 🔧 Configure your profiles here
PROFILES = {
    "personal": {
        "folder": "pessoal",
        "git_name": "Geovane C.",
        "git_email": "geovanent@gmail.com",
    },
    "Customer1": {
        "folder": "customer1",
        "git_name": "Geovane C.",
        "git_email": "customer1@example.com",
        "sign_commits": True,  # Enable SSH commit signing
    },
    "Customer2": {
        "folder": "customer2",
        "git_name": "Geovane C.",
        "git_email": "customer2@example.com",
    },
    # Add new clients here, e.g.:
    # "clientX": {
    #     "folder": "clientX",
    #     "git_name": "Geovane (Client X)",
    #     "git_email": "your.email@clientx.com",
    # },
}


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


def configure_git(profile_name: str):
    """Configure Git identity (user.name & user.email) locally and commit signing globally."""
    profile = PROFILES.get(profile_name, {})
    git_name = profile.get("git_name")
    git_email = profile.get("git_email")
    sign_commits = profile.get("sign_commits", False)

    if not git_name and not git_email and not sign_commits:
        return

    # Configure commit signing globally (doesn't require being in a Git repo)
    if sign_commits:
        pub_key_path = os.path.join(PATH_SSH, KEY_NAME + ".pub")
        if os.path.exists(pub_key_path):
            # Update allowed_signers file
            if update_allowed_signers(profile_name):
                # Configure Git to use the allowed_signers file
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

            subprocess.run(
                ["git", "config", "--global", "commit.gpgsign", "true"], check=False
            )
            subprocess.run(
                ["git", "config", "--global", "tag.gpgsign", "true"], check=False
            )
            subprocess.run(
                ["git", "config", "--global", "gpg.format", "ssh"], check=False
            )
            subprocess.run(
                ["git", "config", "--global", "user.signingkey", pub_key_path],
                check=False,
            )
            print(f"🔐 Commit signing enabled globally (SSH) for profile: {profile_name}")
        else:
            print(
                f"⚠️  WARNING: SSH public key not found at {pub_key_path}. "
                "Commit signing not configured."
            )
    else:
        # Disable commit signing globally for profiles that don't require it
        subprocess.run(
            ["git", "config", "--global", "--unset", "commit.gpgsign"],
            check=False,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "config", "--global", "--unset", "tag.gpgsign"],
            check=False,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "config", "--global", "--unset", "gpg.format"],
            check=False,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "config", "--global", "--unset", "user.signingkey"],
            check=False,
            stderr=subprocess.DEVNULL,
        )
        # Note: We keep gpg.ssh.allowedSignersFile configured even when signing is disabled
        # so it's available for verification of existing signed commits

    # Configure user.name and user.email locally (requires being in a Git repo)
    if git_name or git_email:
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except subprocess.CalledProcessError:
            print("ℹ️  Not inside a Git repository. Skipping local Git identity update.")
            print(
                f"   To configure this repository, run the script from inside the repo:\n"
                f"   cd /path/to/repo && python {os.path.join(PATH_SSH, 'change_keys.py')} -p {profile_name}"
            )
            return

        # Show current configuration before updating
        current_name = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        current_email = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        
        if current_name or current_email:
            print(f"   Current Git config: {current_name or '(not set)'} <{current_email or '(not set)'}>")

        # Configure user.name and user.email locally (without --global flag)
        if git_name:
            result = subprocess.run(
                ["git", "config", "user.name", git_name],
                check=False,
                capture_output=True,
            )
            if result.returncode == 0:
                print(f"   ✓ Git user.name set to: {git_name}")
            else:
                print(f"   ⚠️  Failed to set Git user.name: {result.stderr.decode().strip()}")
        
        if git_email:
            result = subprocess.run(
                ["git", "config", "user.email", git_email],
                check=False,
                capture_output=True,
            )
            if result.returncode == 0:
                print(f"   ✓ Git user.email set to: {git_email}")
            else:
                print(f"   ⚠️  Failed to set Git user.email: {result.stderr.decode().strip()}")

    print(f"🧾 Git identity updated for profile: {profile_name}\n")


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
    args = parser.parse_args()

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