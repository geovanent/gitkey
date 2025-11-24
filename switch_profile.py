"""
==============================================
 SSH MULTI PROFILE MANAGER - USER MANUAL
==============================================

This script allows switching between multiple SSH profiles,
each with its own SSH key and Git identity (user.name & user.email).

Ideal for consultants working with many clients/projects.

----------------------------------------------
 📌 EXPECTED FOLDER STRUCTURE (inside ~/.ssh/)
----------------------------------------------

~/.ssh/
    switch_profile.py
    active_profile.lock
    id_ed25519               <-- active SSH key (overwritten by the script)
    id_ed25519.pub
    personal/
        id_ed25519
        id_ed25519.pub
    client1/
        id_ed25519
        id_ed25519.pub
    client2/
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
        "git_email": "your.email@clientx.com"
    }

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
KEY_NAME = "id_ed25519"


# 🔧 Configure your profiles here
PROFILES = {
    "personal": {
        "folder": "personal",
        "git_name": "Geovane C.",
        "git_email": "geovanent@gmail.com",
    },
    "Customer1": {
        "folder": "customer1",
        "git_name": "Geovane C.",
        "git_email": "customer1@example.com",
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


def configure_git(profile_name: str):
    """Configure Git identity (user.name & user.email) for the current repository."""
    profile = PROFILES.get(profile_name, {})
    git_name = profile.get("git_name")
    git_email = profile.get("git_email")

    if not git_name and not git_email:
        return

    # Check if inside a Git repo
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError:
        print("ℹ️  Not inside a Git repository. Skipping Git identity update.")
        return

    if git_name:
        subprocess.run(["git", "config", "user.name", git_name], check=False)
    if git_email:
        subprocess.run(["git", "config", "user.email", git_email], check=False)

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
