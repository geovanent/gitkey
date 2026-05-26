# Configuration

## settings.py

Copy from the example on first install (the installer does this automatically):

```sh
cp ~/.ssh/gitkey/settings-example.py ~/.ssh/gitkey/settings.py
```

### Profile fields

| Field | Required | Description |
|-------|----------|-------------|
| `folder` | yes | Subfolder under `~/.ssh/` with `id_ed25519` |
| `git_name` | yes | Git `user.name` |
| `git_email` | yes | Git `user.email` |
| `sign_commits` | no | `True` to enable SSH commit signing |

### Example

```python
GIT_GLOBAL_SCOPE = True  # False = Git config only in current repo

PROFILES = {
    "personal": {
        "folder": "personal",
        "git_name": "Your Name",
        "git_email": "you@example.com",
    },
    "clientA": {
        "folder": "clientA",
        "git_name": "Your Name (Client A)",
        "git_email": "dev@clienta.com",
        "sign_commits": True,
    },
}
```

## Folder layout

```text
~/.ssh/
├── gitkey/
│   ├── switch_profile.py
│   ├── settings.py
│   └── repo_bindings.json    # auto-generated (per-repo mode)
├── personal/
│   ├── id_ed25519
│   └── id_ed25519.pub
├── clientA/
│   ├── id_ed25519
│   └── id_ed25519.pub
├── id_ed25519              # active key (global mode)
├── active_profile.lock     # last profile used
└── allowed_signers         # commit signing (auto-generated)
```

## Add a new profile

```sh
mkdir ~/.ssh/clientX
ssh-keygen -t ed25519 -C "you@clientx.com" -f ~/.ssh/clientX/id_ed25519
```

Then add to `settings.py`:

```python
"clientX": {
    "folder": "clientX",
    "git_name": "Your Name (Client X)",
    "git_email": "you@clientx.com",
},
```

Add the public key to GitHub/GitLab as an **Authentication Key**.

## Global vs local Git config

| `GIT_GLOBAL_SCOPE` | Effect |
|--------------------|--------|
| `True` (default) | `user.name` / `user.email` set globally |
| `False` | Only the current Git repository |

Per-repo bindings (`gitkey --bind`) always use **local** config regardless of this setting.
