<p align="center">
  <img src="assets/brand/banner.png" alt="gitkey - SSH keys and Git identity in one command" width="920">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-00D4AA?style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.8+-22D3EE?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-6366F1?style=flat-square" alt="Platform">
</p>

<p align="center">
  <img src="assets/demo/demo.gif" alt="gitkey demo — switch profile and bind repository" width="720">
</p>

---

## What it does

| Mode | Command | Use when |
|:----:|---------|----------|
| 🌐 **Global** | `gitkey -p personal` | One active SSH key for everything |
| 📁 **Per repo** | `gitkey --bind -p clientA` | Several repos open at once, each with its own key |

```text
~/.ssh/
├── gitkey/              ← this tool
├── personal/id_ed25519
├── clientA/id_ed25519
└── id_ed25519           ← active key (global mode)
```

Pure Python · no extra runtime dependencies · macOS, Linux, WSL & Windows

---

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/geovanent/gitkey/main/install.sh | bash
```

<details>
<summary>Other platforms & manual install</summary>

**From clone (macOS / Linux / WSL):**

```sh
git clone git@github.com:geovanent/gitkey.git ~/.ssh/gitkey
cd ~/.ssh/gitkey && ./install
```

**Windows (PowerShell):**

```powershell
git clone git@github.com:geovanent/gitkey.git $env:USERPROFILE\.ssh\gitkey
cd $env:USERPROFILE\.ssh\gitkey
powershell -ExecutionPolicy Bypass -File install.ps1
```

</details>

---

## Quick start

**1.** Edit `~/.ssh/gitkey/settings.py`:

```python
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
    },
}
```

**2.** Create keys:

```sh
ssh-keygen -t ed25519 -f ~/.ssh/personal/id_ed25519 -C "you@example.com"
ssh-keygen -t ed25519 -f ~/.ssh/clientA/id_ed25519 -C "dev@clienta.com"
```

**3.** Go:

```sh
gitkey -p personal          # global switch
gitkey --bind -p clientA    # this repo only
```

---

## Usage

<table>
<tr><td><b>Global switch</b></td><td>

```sh
gitkey -p personal
gitkey -p auto              # rotate profiles
gitkey -p clientA --no-git  # SSH only
gitkey --reset / gitkey -f  # fix last commit
```

</td></tr>
<tr><td><b>Per-repository</b></td><td>

```sh
gitkey --bind -p clientA
gitkey --binds
gitkey --unbind
gitkey --bind -p clientA -r ~/work/client
```

</td></tr>
</table>

| Flag | Description |
|------|-------------|
| `-p`, `--profile` | Profile name or `auto` |
| `--bind` / `--unbind` / `--binds` | Per-repo SSH + Git config |
| `-r`, `--recursive` | Bind every repo under a path |
| `--no-git` | SSH key only |
| `-h`, `--help` | Full help |

---

## Documentation

| | |
|---|---|
| [Configuration](docs/configuration.md) | Profiles, folders, new clients |
| [Commit signing](docs/commit-signing.md) | SSH signatures on GitHub |
| [Troubleshooting](docs/troubleshooting.md) | Common fixes |
| [Brand assets](docs/brand.md) | Colors, logos, regenerate GIF |

---

<p align="center">
  <sub>MIT License · <a href="https://github.com/geovanent/gitkey">github.com/geovanent/gitkey</a></sub><br>
  <sub>If this helps you, consider starring the repo</sub>
</p>
