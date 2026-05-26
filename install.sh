#!/usr/bin/env bash
# gitkey installer — macOS, Linux, WSL
set -euo pipefail

REPO_URL="git@github.com:geovanent/gitkey.git"
INSTALL_DIR="${HOME}/.ssh/gitkey"
BIN_DIR="${HOME}/.local/bin"
PATH_MARKER="# added by gitkey installer"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

info()  { printf '\033[36m→\033[0m %s\n' "$*"; }
ok()    { printf '\033[32m✓\033[0m %s\n' "$*"; }
warn()  { printf '\033[33m!\033[0m %s\n' "$*" >&2; }
die()   { printf '\033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

detect_os() {
  case "$(uname -s)" in
    Darwin) echo "macOS" ;;
    Linux)  echo "Linux" ;;
    *)      echo "$(uname -s)" ;;
  esac
}

require_python() {
  command -v python3 &>/dev/null || die "Python 3 is required."
}

require_git() {
  command -v git &>/dev/null || die "Git is required to clone the repository."
}

same_dir() {
  local a b
  a="$(cd "$1" && pwd -P)"
  b="$(cd "$2" 2>/dev/null && pwd -P)" || return 1
  [[ "$a" == "$b" ]]
}

has_app() {
  [[ -f "$1/lib/switch_profile.py" ]]
}

ensure_repo() {
  if [[ -d "${INSTALL_DIR}/.git" ]]; then
    info "Updating ${INSTALL_DIR}..."
    git -C "${INSTALL_DIR}" pull --ff-only 2>/dev/null \
      || git -C "${INSTALL_DIR}" pull 2>/dev/null \
      || warn "Could not update via git pull; continuing."
  elif has_app "${REPO_ROOT}" && same_dir "${REPO_ROOT}" "${INSTALL_DIR}"; then
    info "Using existing installation at ${INSTALL_DIR}"
  elif has_app "${REPO_ROOT}"; then
    info "Installing from ${REPO_ROOT}..."
    mkdir -p "${INSTALL_DIR}"
    if command -v rsync &>/dev/null; then
      rsync -a \
        --exclude '.git' \
        --exclude 'settings.py' \
        --exclude 'repo_bindings.json' \
        --exclude '__pycache__' \
        "${REPO_ROOT}/" "${INSTALL_DIR}/"
    else
      cp -R "${REPO_ROOT}/." "${INSTALL_DIR}/"
    fi
  else
    require_git
    info "Cloning into ${INSTALL_DIR}..."
    mkdir -p "$(dirname "${INSTALL_DIR}")"
    git clone "${REPO_URL}" "${INSTALL_DIR}"
  fi
}

setup_settings() {
  local example="${INSTALL_DIR}/lib/settings-example.py"
  local settings="${INSTALL_DIR}/settings.py"
  if [[ ! -f "${settings}" ]]; then
    cp "${example}" "${settings}"
    ok "Created ${settings}"
  else
    ok "Keeping existing ${settings}"
  fi
}

link_cli() {
  mkdir -p "${BIN_DIR}"
  ln -sf "${INSTALL_DIR}/gitkey" "${BIN_DIR}/gitkey"
  chmod +x "${INSTALL_DIR}/gitkey" "${INSTALL_DIR}/lib/switch_profile.py" 2>/dev/null || true
  ok "Linked gitkey → ${BIN_DIR}/gitkey"
}

ensure_path() {
  local rc shell_name="${SHELL##*/}"
  case "${shell_name}" in
    zsh)  rc="${HOME}/.zshrc" ;;
    bash) rc="${HOME}/.bashrc" ;;
    *)    rc="" ;;
  esac

  if echo ":${PATH}:" | grep -q ":${BIN_DIR}:"; then
    ok "PATH already includes ${BIN_DIR}"
    return 0
  fi

  if [[ -n "${rc}" ]] && [[ -f "${rc}" ]] && grep -qF "${PATH_MARKER}" "${rc}" 2>/dev/null; then
    ok "PATH entry already in ${rc}"
    return 0
  fi

  if [[ -n "${rc}" ]]; then
    {
      echo ""
      echo "${PATH_MARKER}"
      echo "export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    } >> "${rc}"
    ok "Added ${BIN_DIR} to PATH in ${rc}"
    warn "Run: source ${rc}"
  else
    warn "Add to your shell profile: export PATH=\"\${HOME}/.local/bin:\${PATH}\""
  fi
}

verify() {
  export PATH="${BIN_DIR}:${PATH}"
  command -v gitkey &>/dev/null || die "gitkey not found in PATH after install"
  gitkey --help >/dev/null
  ok "gitkey is ready"
}

main() {
  echo ""
  echo "  gitkey installer ($(detect_os))"
  echo "  ─────────────────────────────"
  echo ""

  require_python
  ensure_repo
  setup_settings
  link_cli
  ensure_path
  verify

  echo ""
  ok "Installation complete"
  echo ""
  echo "  Next steps:"
  echo "    1. Edit ~/.ssh/gitkey/settings.py"
  echo "    2. ssh-keygen -t ed25519 -f ~/.ssh/<profile>/id_ed25519"
  echo "    3. gitkey"
  echo ""
}

main "$@"
