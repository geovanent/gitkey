# 🛡️ SSH and GIT Multi-Profile Manager
Easily switch between multiple SSH identities and Git profiles  
Perfect for consultants, freelancers, and developers with multiple clients.

------------------------------------------------------------
📌 OVERVIEW
------------------------------------------------------------
SSH Multi-Profile Manager is a lightweight Python script that allows you to switch between multiple SSH key profiles and Git identities with a single command.

It automates:
- Replacing your active SSH key (id_ed25519)
- Setting your Git user.name and user.email
- Cycling automatically through profiles
- Remembering the last active profile

Simple, fast, and dependency-free.

------------------------------------------------------------
🚀 FEATURES
------------------------------------------------------------
- Supports unlimited SSH profiles
- Auto-rotation between profiles
- Updates Git identity per project
- No dependencies (pure Python)
- Safe permissions (600 on private key)
- Works on macOS, Linux, WSL

------------------------------------------------------------
🗂 HOW CREATE A NEW CUSTOMER
------------------------------------------------------------
```sh
ssh-keygen -t ed25519 -C "geovane.clientx@example.com" -f ~/.ssh/clientX/id_ed25519
```

------------------------------------------------------------
🗂 FOLDER STRUCTURE
------------------------------------------------------------
Place the script and keys like this inside ~/.ssh:

```sh
~/.ssh/
    switch_profile.py
    active_profile.lock
    id_ed25519
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
```

------------------------------------------------------------
📥 INSTALLATION
------------------------------------------------------------
Clone the project:

```sh
git clone https://github.com/<your-name>/ssh-multi-profile-manager.git
cd ssh-multi-profile-manager
```

Make executable:

```sh
chmod +x switch_profile.py
```

Move script into ~/.ssh:

```sh
mv switch_profile.py ~/.ssh/
```

(Optional) Create a global command:

```sh
sudo ln -s ~/.ssh/switch_profile.py /usr/local/bin/sshprofile
```

Now you can run:

```sh
sshprofile -p personal
```

------------------------------------------------------------
⚙ CONFIGURATION
------------------------------------------------------------
Profiles are defined inside the script:

```sh
PROFILES = {
    "personal": {
        "folder": "personal",
        "git_name": "Your Name (Personal)",
        "git_email": "you.personal@example.com"
    },
    "clientA": {
        "folder": "clientA",
        "git_name": "Your Name (Client A)",
        "git_email": "dev@clientA.com"
    }
}
```

Fields:
- folder: Subfolder inside ~/.ssh where keys are stored
- git_name: Git username for commits
- git_email: Git email for commits

------------------------------------------------------------
➕ ADDING A NEW CLIENT
------------------------------------------------------------
1. Create a folder:
    mkdir ~/.ssh/clientX

2. Add your SSH key pair inside:
    ~/.ssh/clientX/id_ed25519
    ~/.ssh/clientX/id_ed25519.pub

3. Add profile entry to the script:

"clientX": {
    "folder": "clientX",
    "git_name": "Your Name (Client X)",
    "git_email": "you@clientx.com"
}

------------------------------------------------------------
🖥 USAGE
------------------------------------------------------------
Switch to a specific profile:
    python ~/.ssh/switch_profile.py -p toro

Auto-rotate between profiles:
    python ~/.ssh/switch_profile.py

Rotation order is alphabetical:
    personal -> santander -> toro -> clientX -> personal -> ...

Switch SSH key only (skip Git identity):
    python ~/.ssh/switch_profile.py -p santander --no-git

------------------------------------------------------------
🔒 SECURITY
------------------------------------------------------------
- Private keys are set to 600 permissions
- No external connections or telemetry
- Everything stays local in ~/.ssh
- Code is fully auditable

------------------------------------------------------------
🧪 ROADMAP
------------------------------------------------------------
- Add interactive menu (fzf)
- macOS notifications
- Windows PowerShell port
- External JSON/YAML config support
- Unit tests
- GitHub/GitLab auto-detection plugin

------------------------------------------------------------
🤝 CONTRIBUTING
------------------------------------------------------------
Contributions are welcome!
Open an issue first to discuss major changes.

------------------------------------------------------------
📝 LICENSE
------------------------------------------------------------
MIT License — free to use, modify, and distribute.

------------------------------------------------------------
⭐ SUPPORT
------------------------------------------------------------
If this project helps you, please star the repository to support development!
