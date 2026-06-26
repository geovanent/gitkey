# Troubleshooting

## `gitkey: command not found`

Re-run the installer or reload your shell:

```sh
cd ~/.ssh/gitkey && ./install
source ~/.zshrc   # or ~/.bashrc
```

Check the symlink:

```sh
ls -la ~/.local/bin/gitkey
echo $PATH | tr ':' '\n' | grep local/bin
```

## `switch_profile.py not found`

The CLI looks for the script in:

- `~/.ssh/gitkey/lib/switch_profile.py`
- `~/.ssh/gitkey/switch_profile.py` (legacy)
- `~/.ssh/switch_profile.py` (legacy)

Reinstall into the default location:

```sh
git clone git@github.com:geovanent/gitkey.git ~/.ssh/gitkey
cd ~/.ssh/gitkey && ./install
```

## Profile / keys not found

```sh
ls ~/.ssh/<folder>/id_ed25519*
```

Ensure the profile exists in `settings.py` and the `folder` name matches the directory.

## Permission denied on private key

```sh
chmod 600 ~/.ssh/<folder>/id_ed25519
chmod +x ~/.ssh/gitkey/gitkey
```

## Python not found

```sh
python3 --version
# macOS: brew install python3
# Ubuntu: sudo apt install python3
```

## Bind not working for a repo

```sh
gitkey --binds
git -C /path/to/repo config --local core.sshCommand
gitkey --bind -p <profile>    # run again inside the repo
```

## Windows notes

Native Windows ships a `gitkey.cmd` shim that calls `python`.

Quick notes:

- To install natively with PowerShell, run the included installer `install.ps1` (see [Windows Installation](docs/install-windows.md)).
- If PowerShell blocks scripts, run the installer with `-ExecutionPolicy Bypass` or set `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
- For best compatibility with SSH agents and signing, prefer **WSL** or **Git Bash** and use the Unix installer (`install.sh`).
