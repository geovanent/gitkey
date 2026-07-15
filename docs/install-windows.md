# Windows installation

This guide covers installing gitkey on native Windows using PowerShell, and alternatives using Git Bash or WSL.

## Prerequisites

- Git for Windows (git), or WSL/Git Bash for a Unix-like shell
- Python 3.8+ available on PATH

## Install (PowerShell)

Copy-paste this one-liner:

```powershell
irm https://raw.githubusercontent.com/geovanent/gitkey/main/install.ps1 -OutFile $env:TEMP\gitkey-install.ps1; powershell -ExecutionPolicy Bypass -File $env:TEMP\gitkey-install.ps1
```

Then **fully restart Cursor / open a new PowerShell window outside Cursor** and run `gitkey`.

Integrated terminals often keep the old PATH until the app restarts. Until then:

```powershell
& "$env:USERPROFILE\.local\bin\gitkey.cmd"
```

If you already cloned the repo:

```powershell
cd $env:USERPROFILE\.ssh\gitkey
.\install.cmd
```

Optional — allow local PowerShell scripts (profiles, `.ps1`) for your user:

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
