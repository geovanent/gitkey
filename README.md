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
- Enabling SSH commit signing for profiles that require it
- Cycling automatically through profiles
- Remembering the last active profile

Simple, fast, and dependency-free.

------------------------------------------------------------
🚀 FEATURES
------------------------------------------------------------
- Supports unlimited SSH profiles
- Auto-rotation between profiles
- Updates Git identity per project
- SSH commit signing support (Git 2.34+)
- Automatic allowed_signers file management
- No dependencies (pure Python)
- Safe permissions (600 on private key)
- Works on macOS, Linux, WSL

------------------------------------------------------------
🗂 HOW TO CREATE A NEW CUSTOMER
------------------------------------------------------------
```sh
ssh-keygen -t ed25519 -C "geovane.clientx@example.com" -f ~/.ssh/clientX/id_ed25519
```

------------------------------------------------------------
🗂 FOLDER STRUCTURE
------------------------------------------------------------
After cloning the repository into `~/.ssh/`, your structure should look like this:

```sh
~/.ssh/
    # Repository files
    ssh-multi-profile-manager/    # or your chosen folder name
        switch_profile.py
        change_keys               # CLI wrapper script (executable)
        README.md
    
    # Auto-generated files (created by the script)
    active_profile.lock
    allowed_signers                # Auto-generated file for SSH commit signing
    id_ed25519                    # Active SSH key (overwritten by script)
    id_ed25519.pub
    
    # Profile folders (one per client/profile)
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

**Note:** The script automatically creates `active_profile.lock` and `allowed_signers` in `~/.ssh/` when first run. Profile folders should be created manually as needed.

------------------------------------------------------------
📥 INSTALLATION
------------------------------------------------------------

### Quick Install (Recommended)

1. **Clone the repository into `~/.ssh/`:**
   ```sh
   cd ~/.ssh
   git clone git@github.com:geovanent/switch_profile_git.git
   # Or if you prefer a different name:
   git clone git@github.com:geovanent/switch_profile_git.git switch_profile_git
   ```

2. **Make the wrapper script executable:**
   ```sh
   chmod +x ~/.ssh/ssh-multi-profile-manager/change_keys
   # Or if you used a different folder name:
   chmod +x ~/.ssh/switch_profile_git/change_keys
   ```

3. **Create a symlink to make it globally accessible:**

   **Option A: Using /usr/local/bin (macOS/Linux - requires sudo):**
   ```sh
   sudo ln -s ~/.ssh/ssh-multi-profile-manager/change_keys /usr/local/bin/change_keys
   ```

   **Option B: Using ~/.local/bin (Linux - no sudo needed):**
   ```sh
   mkdir -p ~/.local/bin
   ln -s ~/.ssh/ssh-multi-profile-manager/change_keys ~/.local/bin/change_keys
   # Add to PATH if not already there (add to ~/.bashrc or ~/.zshrc):
   export PATH="$HOME/.local/bin:$PATH"
   ```

   **Option C: Add to PATH directly (macOS/Linux):**
   Add this line to your `~/.zshrc` (macOS) or `~/.bashrc`/`~/.zshrc` (Linux):
   ```sh
   export PATH="$HOME/.ssh/ssh-multi-profile-manager:$PATH"
   ```
   Then reload your shell:
   ```sh
   source ~/.zshrc  # or source ~/.bashrc
   ```

4. **Verify installation:**
   ```sh
   change_keys --help
   ```

Now you can use `change_keys` from anywhere:

```sh
change_keys -p personal
change_keys -p auto
change_keys --no-git
```

### Manual Install (Alternative)

If you prefer to install manually without the wrapper:

1. **Clone or download the repository:**
   ```sh
   cd ~/.ssh
   git clone git@github.com:geovanent/switch_profile_git.git
   ```

2. **Make the Python script executable:**
   ```sh
   chmod +x ~/.ssh/ssh-multi-profile-manager/change_keys.py
   ```

3. **Create an alias (add to `~/.zshrc` or `~/.bashrc`):**
   ```sh
   alias change_keys='python3 ~/.ssh/ssh-multi-profile-manager/switch_profile.py'
   ```

4. **Reload your shell:**
   ```sh
   source ~/.zshrc  # or source ~/.bashrc
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
- sign_commits: (Optional) Set to `True` to enable SSH commit signing for this profile

Example with commit signing:
```python
PROFILES = {
    "personal": {
        "folder": "personal",
        "git_name": "Your Name (Personal)",
        "git_email": "you.personal@example.com"
    },
    "clientA": {
        "folder": "clientA",
        "git_name": "Your Name (Client A)",
        "git_email": "dev@clientA.com",
        "sign_commits": True  # Enable SSH commit signing
    }
}
```

------------------------------------------------------------
➕ ADDING A NEW CLIENT
------------------------------------------------------------
1. Create a folder:
   ```sh
    mkdir ~/.ssh/clientX
   ```

2. Generate SSH key pair:
   ```sh
    ssh-keygen -t ed25519 -C "your.email@clientx.com" -f ~/.ssh/clientX/id_ed25519
    ```

3. Add profile entry to the script:
```python
"clientX": {
    "folder": "clientX",
    "git_name": "Your Name (Client X)",
    "git_email": "you@clientx.com",
    "sign_commits": False  # Set to True if you want SSH commit signing
}
```

**For profiles with commit signing enabled:**
- The script automatically updates the `allowed_signers` file
- Configures Git globally to use SSH signing
- Sets `commit.gpgsign` and `tag.gpgsign` to `true`
- Uses the active SSH key for signing commits

**Note:** When switching to a profile without `sign_commits: True`, commit signing is automatically disabled globally.

------------------------------------------------------------
🖥 USAGE
------------------------------------------------------------

After installation, use the `change_keys` command from anywhere:

**Switch to a specific profile:**
```sh
change_keys -p toro
change_keys -p personal
change_keys -p clientX
```

**Interactive mode (shows menu to choose):**
```sh
change_keys
```

**Auto-rotate between profiles (alphabetical order):**
```sh
change_keys -p auto
```
Rotation order is alphabetical:
    personal -> santander -> toro -> clientX -> personal -> ...

**Switch SSH key only (skip Git identity):**
```sh
change_keys -p santander --no-git
```

**Show help:**
```sh
change_keys --help
```

**Note:** If you didn't install the wrapper script, you can still use:
```sh
python3 ~/.ssh/ssh-multi-profile-manager/switch_profile.py -p personal
```

------------------------------------------------------------
🔐 SSH COMMIT SIGNING
------------------------------------------------------------
The script supports SSH commit signing (requires Git 2.34+).

**How it works:**
1. When a profile has `sign_commits: True`, the script:
   - Updates the `allowed_signers` file with the profile's email and public key
   - Configures Git globally to use SSH signing
   - Sets the active SSH key as the signing key

2. The `allowed_signers` file format:
   ```
   email@example.com ssh-ed25519 AAAA...keydata...
   ```

3. Git configuration set automatically:
   - `commit.gpgsign = true`
   - `tag.gpgsign = true`
   - `gpg.format = ssh`
   - `gpg.ssh.allowedSignersFile = ~/.ssh/allowed_signers`
   - `user.signingkey = ~/.ssh/id_ed25519.pub`

**Adding a new signing key (step by step):**

1. **Create the profile folder:**
   ```sh
   mkdir ~/.ssh/clientX
   ```

2. **Generate SSH key pair:**
   ```sh
   ssh-keygen -t ed25519 -C "your.email@clientx.com" -f ~/.ssh/clientX/id_ed25519
   ```
   - Press Enter to accept default passphrase (or set one if preferred)
   - This creates both `id_ed25519` (private) and `id_ed25519.pub` (public)

3. **Add the profile to the script:**
   Edit `change_keys.py` and add:
   ```python
   "clientX": {
       "folder": "clientX",
       "git_name": "Your Name (Client X)",
       "git_email": "your.email@clientx.com",
       "sign_commits": True  # Enable SSH commit signing
   }
   ```

4. **Switch to the profile:**
   ```sh
   change_keys -p clientX
   ```
   The script will automatically:
   - Copy the SSH keys to `~/.ssh/id_ed25519` and `~/.ssh/id_ed25519.pub`
   - Update `~/.ssh/allowed_signers` with your email and public key
   - Configure Git globally for SSH commit signing
   - Set your Git identity locally (if inside a Git repository)

5. **Verify the setup:**
   ```sh
   # Check Git signing configuration
   git config --global --get commit.gpgsign
   git config --global --get gpg.format
   git config --global --get user.signingkey
   
   # Check allowed_signers file
   cat ~/.ssh/allowed_signers
   ```

6. **Add the public key to GitHub (for commit verification):**
   
   **Important:** To have your signed commits recognized and displayed correctly on GitHub, you need to add the public key as a **Signing Key**, not just as a regular SSH key.
   
   a. Copy your public key:
      ```sh
      cat ~/.ssh/id_ed25519.pub
      # or
      cat ~/.ssh/clientX/id_ed25519.pub
      ```
   
   b. Go to GitHub → Settings → SSH and GPG keys
   
   c. Click **"New SSH key"**
   
   d. Fill in:
      - **Title:** e.g., "Client X Signing Key"
      - **Key type:** Select **"Signing Key"** (not "Authentication Key")
      - **Key:** Paste your public key content
   
   e. Click **"Add SSH key"**
   
   **Note:** You can add the same key as both Authentication Key (for git operations) and Signing Key (for commit verification). They serve different purposes.

7. **Test commit signing:**
   ```sh
   # Make a test commit
   echo "test" > test.txt
   git add test.txt
   git commit -m "Test signed commit"
   
   # Verify the signature locally
   git log --show-signature -1
   ```
   
   After pushing to GitHub, you should see a "Verified" badge on your commits.

**Verifying signed commits:**
```sh
git log --show-signature
```

**Troubleshooting:**

- **Permission errors on `allowed_signers`:**
  ```sh
  chmod 644 ~/.ssh/allowed_signers
  chown $USER ~/.ssh/allowed_signers  # If owned by another user
  ```

- **Check Git version (requires 2.34+):**
  ```sh
  git --version
  ```
  If older, update Git:
  - macOS: `brew install git`
  - Linux: Use your package manager

- **Commit signing not working:**
  ```sh
  # Verify Git config
  git config --global --list | grep -E "(gpgsign|gpg\.format|signingkey)"
  
  # Check if allowed_signers file exists and has correct format
  cat ~/.ssh/allowed_signers
  
  # Verify SSH key is accessible
  ls -la ~/.ssh/id_ed25519*
  ```

- **Commits not showing as "Verified" on GitHub:**
  - Make sure you added the public key to GitHub as a **Signing Key** (not just Authentication Key)
  - Go to GitHub → Settings → SSH and GPG keys
  - Verify the key is listed under "Signing keys" section
  - The email in your Git config (`git config user.email`) must match the email associated with your GitHub account
  - After adding the signing key, new commits will show as verified; old commits won't be retroactively verified

- **Multiple profiles with signing:**
  Each time you switch profiles, the `allowed_signers` file is updated. All signing keys are kept in the file, so you can verify commits from any previously used signing profile.
  
  **Important:** Each profile's public key must be added separately to GitHub as a Signing Key if you want commits from different profiles to show as verified.

- **Disable signing for a specific commit:**
  ```sh
  git commit --no-gpg-sign -m "Unsigned commit"
  ```

------------------------------------------------------------
🔧 TROUBLESHOOTING - CLI Wrapper
------------------------------------------------------------

**Command `change_keys` not found:**
- Verify the symlink was created correctly:
  ```sh
  ls -la /usr/local/bin/change_keys  # Option A
  ls -la ~/.local/bin/change_keys     # Option B
  ```
- Check if the directory is in your PATH:
  ```sh
  echo $PATH | grep -E "(/usr/local/bin|~/.local/bin)"
  ```
- For Option C (direct PATH), verify your shell config file was reloaded:
  ```sh
  source ~/.zshrc  # or source ~/.bashrc
  ```

**Script not found error:**
- The wrapper looks for `switch_profile.py` in these locations:
  - `~/.ssh/switch_profile.py`
  - `~/.ssh/ssh-multi-profile-manager/switch_profile.py`
  - `~/.ssh/switch_profile_git/switch_profile.py`
  - `~/.ssh/ssh-profile-manager/switch_profile.py`
- If your repository is in a different location, either:
  - Move it to one of the locations above, or
  - Create a symlink: `ln -s /path/to/repo/switch_profile.py ~/.ssh/switch_profile.py`

**Permission denied:**
- Make sure the wrapper script is executable:
  ```sh
  chmod +x ~/.ssh/ssh-multi-profile-manager/change_keys
  ```

**Python not found:**
- Ensure Python 3 is installed:
  ```sh
  python3 --version
  ```
- Install if needed:
  - macOS: `brew install python3`
  - Linux: `sudo apt install python3` (Debian/Ubuntu) or `sudo yum install python3` (RHEL/CentOS)

------------------------------------------------------------
🔒 SECURITY
------------------------------------------------------------
- Private keys are set to 600 permissions
- `allowed_signers` file has 644 permissions (readable by Git)
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
