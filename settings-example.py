# 🔧 Configure your settings and profiles here
# This is an example file. Copy this to settings.py and fill in your actual data.
# The settings.py file should NOT be committed to git (it's in .gitignore).

# Global Git configuration scope
# True = global (affects all repos), False = local (per-repo only)
# Default: True
GIT_GLOBAL_SCOPE = True

# SSH Profiles configuration
PROFILES = {
    "personal": {
        "folder": "personal",
        "git_name": "Your Name",
        "git_email": "your.email@example.com",
    },
    "client1": {
        "folder": "client1",
        "git_name": "Your Name (Client 1)",
        "git_email": "your.email@client1.com",
        "sign_commits": False,  # Optional: set to True to enable SSH commit signing
    },
    "client2": {
        "folder": "client2",
        "git_name": "Your Name (Client 2)",
        "git_email": "your.email@client2.com",
        "sign_commits": True,  # Enable SSH commit signing
    },
    # Add new clients here, e.g.:
    # "clientX": {
    #     "folder": "clientX",
    #     "git_name": "Your Name (Client X)",
    #     "git_email": "your.email@clientx.com",
    # },
}

