#!/bin/bash
#
# Team 9771 FPRO - Mac Machine Setup
# Installs dev tools SYSTEM-WIDE so every user account gets them.
# Run once per Mac. Kids do NOT need to run this.
#
# Usage:  ./team -> option 6   -or-   ./cli/commands/setup_mac.sh
#         (Do NOT use sudo -- the script prompts for admin password internally)
#

set -e

PYTHON_VERSION="3.13.1"
PYTHON_MAJOR="3.13"
PYTHON_PKG_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.pkg"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/${PYTHON_MAJOR}/bin"

NODE_VERSION="22.14.0"

# Project root is two levels up from cli/commands/
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

pass()  { echo -e "  ${GREEN}[OK]${NC} $1"; }
fail()  { echo -e "  ${RED}[!!]${NC} $1"; }
info()  { echo -e "  ${BLUE}[..]${NC} $1"; }
warn()  { echo -e "  ${YELLOW}[??]${NC} $1"; }

echo ""
echo "========================================"
echo " Team 9771 FPRO - Mac Machine Setup"
echo "========================================"
echo ""
echo "This installs tools SYSTEM-WIDE (all user accounts):"
echo "  - Python $PYTHON_VERSION"
echo "  - Node.js $NODE_VERSION"
echo "  - GitHub CLI (gh)"
echo "  - Claude Code"
echo ""
echo -e "${BOLD}Run this once per Mac. Kids don't need to run this.${NC}"
echo ""

# -----------------------------------------------
# Refuse to run as root (common mistake)
# -----------------------------------------------
if [ "$EUID" -eq 0 ]; then
    fail "Do NOT run this script with sudo."
    echo "       Just run:  ./team -> option 6"
    echo "       The script will ask for an admin password when needed."
    exit 1
fi

# -----------------------------------------------
# Pre-cache sudo so we only get one password prompt
# -----------------------------------------------
echo "This script needs admin access. Enter admin password when prompted."
echo ""
sudo -v
# Keep sudo alive in the background
while true; do sudo -n true; sleep 50; kill -0 "$$" 2>/dev/null || exit; done &
SUDO_KEEPALIVE_PID=$!
trap "kill $SUDO_KEEPALIVE_PID 2>/dev/null" EXIT

echo ""

# ===============================================
# Step 1: Remove old Python versions
# ===============================================
echo "--- Step 1: Clean up old Python versions ---"

# Remove Homebrew Python (per-user, causes conflicts with our global install)
if command -v brew &> /dev/null; then
    for pyver in python python@3.8 python@3.9 python@3.10 python@3.11 python@3.12 python@3.14; do
        if brew list "$pyver" &> /dev/null; then
            info "Removing Homebrew $pyver..."
            brew uninstall --ignore-dependencies "$pyver" 2>/dev/null || true
        fi
    done
fi

# Remove old python.org framework installations
for version in 3.8 3.9 3.10 3.11 3.12 3.14; do
    if [ -d "/Library/Frameworks/Python.framework/Versions/$version" ]; then
        info "Removing Python $version framework..."
        sudo rm -rf "/Library/Frameworks/Python.framework/Versions/$version"
    fi
    if [ -d "/Applications/Python $version" ]; then
        sudo rm -rf "/Applications/Python $version"
    fi
done

# Clean up old symlinks
for f in /usr/local/bin/python* /usr/local/bin/pip* /usr/local/bin/idle* /usr/local/bin/pydoc* /usr/local/bin/2to3*; do
    if [ -L "$f" ]; then
        target=$(readlink "$f" 2>/dev/null || true)
        if [[ "$target" == *"Python.framework"* ]] && [[ "$target" != *"$PYTHON_MAJOR"* ]]; then
            sudo rm -f "$f"
        fi
    fi
done

pass "Old Python versions cleaned up"
echo ""

# ===============================================
# Step 2: Install Python 3.13 (system-wide .pkg)
# ===============================================
echo "--- Step 2: Python $PYTHON_VERSION ---"

NEED_PYTHON=true
if [ -x "${PYTHON_BIN}/python3" ]; then
    INSTALLED=$("${PYTHON_BIN}/python3" --version 2>&1)
    if [[ "$INSTALLED" == *"$PYTHON_MAJOR"* ]]; then
        pass "Python $PYTHON_MAJOR already installed ($INSTALLED)"
        NEED_PYTHON=false
    fi
fi

if [ "$NEED_PYTHON" = true ]; then
    info "Downloading Python ${PYTHON_VERSION}..."
    curl -L -o "/tmp/python-${PYTHON_VERSION}.pkg" "$PYTHON_PKG_URL"
    info "Installing Python ${PYTHON_VERSION} system-wide..."
    sudo installer -pkg "/tmp/python-${PYTHON_VERSION}.pkg" -target /
    rm -f "/tmp/python-${PYTHON_VERSION}.pkg"
    pass "Python ${PYTHON_VERSION} installed"
fi

# System-wide PATH entry (applies to ALL users)
sudo bash -c "echo '${PYTHON_BIN}' > /etc/paths.d/python${PYTHON_MAJOR//./}"

# System-wide symlinks (ALL users)
sudo mkdir -p /usr/local/bin
sudo ln -sf "${PYTHON_BIN}/python3" /usr/local/bin/python3
sudo ln -sf "${PYTHON_BIN}/python3" /usr/local/bin/python
sudo ln -sf "${PYTHON_BIN}/pip3" /usr/local/bin/pip3
sudo ln -sf "${PYTHON_BIN}/pip3" /usr/local/bin/pip

export PATH="${PYTHON_BIN}:$PATH"
pass "Python available system-wide for all users"
echo ""

# ===============================================
# Step 3: Install Node.js (system-wide .pkg)
# ===============================================
echo "--- Step 3: Node.js ---"

# Check if node exists at a system-wide path (not Homebrew per-user)
NEED_NODE=true
if [ -x "/usr/local/bin/node" ]; then
    pass "Node.js already installed (/usr/local/bin/node $(node --version 2>/dev/null))"
    NEED_NODE=false
fi

if [ "$NEED_NODE" = true ]; then
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        NODE_PKG_URL="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-arm64.tar.gz"
    else
        NODE_PKG_URL="https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-darwin-x64.tar.gz"
    fi

    info "Downloading Node.js ${NODE_VERSION}..."
    curl -L -o /tmp/node.tar.gz "$NODE_PKG_URL"
    info "Installing Node.js system-wide to /usr/local/..."
    sudo tar -xzf /tmp/node.tar.gz -C /usr/local --strip-components=1
    rm -f /tmp/node.tar.gz
    pass "Node.js installed system-wide ($(/usr/local/bin/node --version))"
fi
echo ""

# ===============================================
# Step 4: Install GitHub CLI (system-wide binary)
# ===============================================
echo "--- Step 4: GitHub CLI (gh) ---"

NEED_GH=true
if [ -x "/usr/local/bin/gh" ]; then
    pass "GitHub CLI already installed (/usr/local/bin/gh)"
    NEED_GH=false
fi

if [ "$NEED_GH" = true ]; then
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        GH_ARCH="macOS_arm64"
    else
        GH_ARCH="macOS_amd64"
    fi

    info "Downloading GitHub CLI..."
    # Get the latest release URL
    GH_LATEST=$(curl -sL "https://api.github.com/repos/cli/cli/releases/latest" | grep "browser_download_url.*${GH_ARCH}.zip" | head -1 | cut -d '"' -f 4)
    if [ -n "$GH_LATEST" ]; then
        curl -L -o /tmp/gh.zip "$GH_LATEST"
        info "Installing GitHub CLI system-wide..."
        cd /tmp
        unzip -qo gh.zip -d gh_extract
        # The zip contains a folder like gh_2.x.x_macOS_arm64/
        GH_DIR=$(ls -d gh_extract/gh_* 2>/dev/null | head -1)
        if [ -n "$GH_DIR" ]; then
            sudo cp "${GH_DIR}/bin/gh" /usr/local/bin/gh
            sudo chmod +x /usr/local/bin/gh
            pass "GitHub CLI installed system-wide"
        else
            fail "Could not extract gh binary"
        fi
        rm -rf /tmp/gh.zip /tmp/gh_extract
        cd "$PROJECT_DIR"
    else
        fail "Could not find gh download URL. Install manually:"
        echo "       https://cli.github.com/"
    fi
fi
echo ""

# ===============================================
# Step 5: Install Claude Code (system-wide npm)
# ===============================================
echo "--- Step 5: Claude Code ---"

if [ -x "/usr/local/bin/claude" ] || command -v claude &> /dev/null; then
    pass "Claude Code already installed"
else
    info "Installing Claude Code system-wide..."
    sudo /usr/local/bin/npm install -g @anthropic-ai/claude-code 2>/dev/null
    if [ -x "/usr/local/bin/claude" ] || command -v claude &> /dev/null; then
        pass "Claude Code installed system-wide"
    else
        warn "Claude Code install may have failed. Try manually:"
        echo "       sudo npm install -g @anthropic-ai/claude-code"
    fi
fi
echo ""

# ===============================================
# Done!
# ===============================================
echo "========================================"
echo -e " ${GREEN}Machine setup complete!${NC}"
echo "========================================"
echo ""
echo "This Mac now has system-wide tools for ALL user accounts."
echo ""
echo "Next: each kid runs the project setup (no admin needed):"
echo ""
echo "  cd $PROJECT_DIR"
echo "  ./team"
echo ""
echo "That gives them a menu for setup, git, testing, and deploy."
echo ""
