#!/usr/bin/env bash
# install_ubuntu.sh — one-script SHYpn setup for Ubuntu Linux
#
# Usage:
#   bash install_ubuntu.sh          # interactive, creates .venv in current dir
#   bash install_ubuntu.sh --check  # only verify an existing install
#
# Supports: Ubuntu 22.04, 24.04 (and derivatives: Mint 21+, PopOS 22.04+)
# Does NOT support: WSL1, non-Ubuntu Debian without adjustment, ARM (untested)

set -euo pipefail

# ── colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET}  $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $*"; }
fail() { echo -e "  ${RED}✗${RESET}  $*"; }
info() { echo -e "     $*"; }
header() { echo -e "\n${BOLD}$*${RESET}"; }

SHYPN_VERSION="2.6.1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

header "SHYpn ${SHYPN_VERSION} — Ubuntu installer"

# ── --check mode: just verify existing install ────────────────────────────────
if [[ "${1:-}" == "--check" ]]; then
    header "Verifying existing installation…"
    if [[ ! -d "${VENV_DIR}" ]]; then
        fail "Virtual environment not found at ${VENV_DIR}"
        info "Run:  bash install_ubuntu.sh"
        exit 1
    fi
    # Delegate to Python headless check
    source "${VENV_DIR}/bin/activate"
    python -m shypn --check
    exit $?
fi

# ── step 0: sanity checks ─────────────────────────────────────────────────────
header "Step 0 — Pre-flight checks"

# Must be run from repo root (where pyproject.toml lives)
if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
    fail "pyproject.toml not found."
    info "Run this script from the shypn repo root directory."
    exit 1
fi
ok "Repo root: ${REPO_ROOT}"

# Not root
if [[ "${EUID}" -eq 0 ]]; then
    fail "Do not run as root. sudo will be used only for apt."
    exit 1
fi

# Detect Ubuntu version
if [[ -f /etc/os-release ]]; then
    source /etc/os-release
    DISTRO_ID="${ID:-unknown}"
    DISTRO_VER="${VERSION_ID:-0}"
else
    DISTRO_ID="unknown"
    DISTRO_VER="0"
fi

case "${DISTRO_ID}" in
    ubuntu|linuxmint|pop)
        ok "Distro: ${PRETTY_NAME:-${DISTRO_ID} ${DISTRO_VER}}"
        ;;
    debian)
        warn "Debian detected (not Ubuntu). Package names may differ slightly."
        ;;
    *)
        warn "Unrecognised distro '${DISTRO_ID}'. Proceeding with Ubuntu package names — may need adjustment."
        ;;
esac

# Python 3.10+
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "${PY_VER}" | cut -d. -f1)
    PY_MINOR=$(echo "${PY_VER}" | cut -d. -f2)
    if (( PY_MAJOR < 3 || (PY_MAJOR == 3 && PY_MINOR < 10) )); then
        fail "Python ${PY_VER} found — SHYpn requires Python 3.10 or later."
        info "Install python3.10+ via: sudo apt install python3.10 python3.10-venv"
        exit 1
    fi
    ok "Python ${PY_VER}"
else
    fail "python3 not found. Install it with: sudo apt install python3 python3-venv"
    exit 1
fi

# Display available? (warn only — --check will give the definitive verdict)
if [[ -n "${DISPLAY:-}" ]] || [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
    ok "Display: ${DISPLAY:-}${WAYLAND_DISPLAY:+ (Wayland: $WAYLAND_DISPLAY)}"
else
    warn "No DISPLAY or WAYLAND_DISPLAY set. GUI will not start in this shell."
    info "This is normal for SSH sessions. Log in to a desktop session to run SHYpn."
fi

# ── step 1: system packages ───────────────────────────────────────────────────
header "Step 1 — System packages (apt)"

# Map Ubuntu version to the correct libgirepository package name.
# Ubuntu < 24.04  → libgirepository1.0-dev
# Ubuntu ≥ 24.04  → libgirepository-1.0-dev  (hyphen instead of dot in major)
VER_NUM=$(echo "${DISTRO_VER}" | tr -d '.' | cut -c1-4)
if (( VER_NUM >= 2404 )); then
    GIR_PKG="libgirepository-1.0-dev"
else
    GIR_PKG="libgirepository1.0-dev"
fi
info "libgirepository package for ${DISTRO_VER}: ${GIR_PKG}"

APT_PACKAGES=(
    python3
    python3-pip
    python3-venv
    python3-gi
    python3-gi-cairo
    gir1.2-gtk-3.0
    gir1.2-glib-2.0
    libgtk-3-dev
    libcairo2-dev
    "${GIR_PKG}"
    pkg-config
    # WeasyPrint system deps (Pango text rendering, fontconfig)
    libpango-1.0-0
    libpangocairo-1.0-0
    fonts-liberation
)

echo ""
info "Packages to install: ${APT_PACKAGES[*]}"
echo ""

# Check which are already installed to avoid needless sudo prompt
MISSING=()
for pkg in "${APT_PACKAGES[@]}"; do
    if ! dpkg-query -W -f='${Status}' "${pkg}" 2>/dev/null | grep -q "install ok installed"; then
        MISSING+=("${pkg}")
    fi
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
    ok "All system packages already installed"
else
    warn "Missing packages: ${MISSING[*]}"
    echo ""
    sudo apt-get update -qq
    sudo apt-get install -y "${MISSING[@]}"
    ok "System packages installed"
fi

# ── step 2: virtual environment ───────────────────────────────────────────────
header "Step 2 — Python virtual environment"

if [[ -d "${VENV_DIR}" ]]; then
    ok "Existing venv found at ${VENV_DIR}"
    warn "Skipping venv creation (delete .venv manually to recreate)"
else
    python3 -m venv "${VENV_DIR}"
    ok "Created venv at ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
ok "Activated: $(python --version)"

# ── step 3: pip packages ──────────────────────────────────────────────────────
header "Step 3 — Python packages (pip)"

python -m pip install --upgrade pip --quiet
ok "pip upgraded"

# Detect install mode: editable (git clone) vs regular (extracted zip)
if [[ -d "${REPO_ROOT}/.git" ]]; then
    INSTALL_FLAG="-e"
    ok "Git repo detected → editable install"
else
    INSTALL_FLAG=""
    ok "No .git directory → regular install (extracted zip)"
fi

python -m pip install ${INSTALL_FLAG:+"${INSTALL_FLAG}"} "${REPO_ROOT}" --quiet
ok "SHYpn ${SHYPN_VERSION} installed"

# ── step 4: headless verification ─────────────────────────────────────────────
header "Step 4 — Headless verification"

python -m shypn --check
EXIT_CODE=$?

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
if [[ ${EXIT_CODE} -eq 0 ]]; then
    echo -e "${BOLD}${GREEN}Installation complete.${RESET}"
    echo ""
    echo "To launch SHYpn:"
    echo "  source ${VENV_DIR}/bin/activate"
    echo "  shypn"
    echo ""
    echo "Or without activating the venv:"
    echo "  ${VENV_DIR}/bin/shypn"
else
    echo -e "${BOLD}${RED}Installation finished with verification errors (see above).${RESET}"
    echo "Check INSTALL.md → Troubleshooting for guidance."
fi

exit ${EXIT_CODE}
