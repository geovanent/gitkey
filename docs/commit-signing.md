# SSH commit signing

Requires **Git 2.34+**.

## Enable for a profile

```python
"clientA": {
    "folder": "clientA",
    "git_name": "Your Name",
    "git_email": "dev@clienta.com",
    "sign_commits": True,
},
```

Then switch or bind:

```sh
gitkey -p clientA
# or
gitkey --bind -p clientA
```

gitkey will:

- Update `~/.ssh/allowed_signers`
- Set `commit.gpgsign`, `gpg.format=ssh`, and `user.signingkey`

## GitHub: add as Signing Key

1. Copy the public key: `cat ~/.ssh/clientA/id_ed25519.pub`
2. GitHub → **Settings** → **SSH and GPG keys** → **New SSH key**
3. Key type: **Signing Key** (not only Authentication Key)
4. The commit email must match your GitHub account email

## Verify

```sh
git log --show-signature -1
```

## Unsigned commit (one-off)

```sh
git commit --no-gpg-sign -m "message"
```

## Troubleshooting

```sh
git --version                    # need 2.34+
git config --global --get gpg.format
cat ~/.ssh/allowed_signers
chmod 644 ~/.ssh/allowed_signers
```

Commits are only marked **Verified** on GitHub after the signing key is registered there.
