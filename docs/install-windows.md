# Windows installation

This guide covers installing gitkey on native Windows using PowerShell, and alternatives using Git Bash or WSL.

## Prerequisites

- Git for Windows (git), or WSL/Git Bash for a Unix-like shell
- Python 3.8+ available on PATH

## Install (PowerShell)

Recommended: run the included PowerShell installer. Open PowerShell (preferably as your user, not Administrator) and run one of the commands below.

One-liner (download, then run as a file — more reliable than `| iex`):

```powershell
$script = Join-Path $env:TEMP 'gitkey-install.ps1'
Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/geovanent/gitkey/main/install.ps1 -OutFile $script
powershell -ExecutionPolicy Bypass -File $script
```

If PowerShell blocks remote scripts, run the installer file explicitly after cloning:

```powershell
git clone https://github.com/geovanent/gitkey.git $env:USERPROFILE\.ssh\gitkey
Set-Location $env:USERPROFILE\.ssh\gitkey
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

If you prefer not to bypass execution policy globally, adjust only the process:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

To allow running local scripts in your user scope (optional):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

## Alternative: Git Bash / WSL

- If you use Git Bash or WSL, you can run the standard installer:

```sh
curl -fsSL https://raw.githubusercontent.com/geovanent/gitkey/main/install.sh | bash
```

This is the recommended path if you need full POSIX SSH tooling and easier parity with macOS/Linux.

## Post-install checks

- Ensure `~/.ssh/gitkey` (Windows: `%USERPROFILE%\.ssh\gitkey`) exists and `gitkey` is on your PATH.
- Verify by running `gitkey --help` or `gitkey --new`.

## Troubleshooting

- If `gitkey` is not found, ensure your local bin directory was linked to a folder on PATH. For PowerShell, check `%USERPROFILE%\.local\bin` or the installer output.
- If SSH signing or agent behaviour is inconsistent on native Windows, prefer Git Bash or WSL for full SSH agent compatibility.
