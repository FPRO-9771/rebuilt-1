#!/bin/bash
#
# Team 9771 FPRO - Project Setup
# Sets up YOUR account to work on the robot code.
# No admin needed. Any team member can run this.
#
# What it does:
#   - Creates/fixes .venv with the right Python
#   - Installs all packages from requirements.txt
#   - Sets up your shell profile (PATH)
#   - Prepares robotpy deploy cache
#   - Sets up git user if needed
#
# Usage:  ./team -> option 2   -or-   ./cli/commands/setup_project.sh
#

set -e

PYTHON_MAJOR="3.13"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/${PYTHON_MAJOR}/bin"

# Project root is two levels up from cli/commands/
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
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
echo " Team 9771 FPRO - Project Setup"
echo "========================================"
echo ""

# -----------------------------------------------
# Pre-check: is Python 3.13 available?
# -----------------------------------------------
if [ ! -x "${PYTHON_BIN}/python3" ]; then
    fail "Python $PYTHON_MAJOR is not installed on this Mac."
    echo ""
    echo "  Ask Brian to run:  ./team -> option 6"
    echo ""
    exit 1
fi
pass "Python $PYTHON_MAJOR found"

cd "$PROJECT_DIR"

# ===============================================
# Step 1: Shell profile
# ===============================================
echo ""
echo "--- Step 1: Shell profile ---"

if [ -f "$HOME/.zshrc" ] || [ "$SHELL" = "/bin/zsh" ]; then
    SHELL_CONFIG="$HOME/.zprofile"
else
    SHELL_CONFIG="$HOME/.bash_profile"
fi

PROFILE_CHANGED=false

# Ensure Python is in PATH
if ! grep -q "Python.framework.*${PYTHON_MAJOR}" "$SHELL_CONFIG" 2>/dev/null; then
    # Clean out any old Python PATH entries first
    if [ -f "$SHELL_CONFIG" ]; then
        sed -i '' '/Python.framework/d' "$SHELL_CONFIG" 2>/dev/null || true
        sed -i '' '/alias python=python3/d' "$SHELL_CONFIG" 2>/dev/null || true
        sed -i '' '/alias pip=pip3/d' "$SHELL_CONFIG" 2>/dev/null || true
        sed -i '' '/# Python.*FPRO/d' "$SHELL_CONFIG" 2>/dev/null || true
    fi
    cat >> "$SHELL_CONFIG" << 'PROFILE_EOF'

# Python 3.13 - Team 9771 FPRO setup
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
alias python=python3
alias pip=pip3
PROFILE_EOF
    PROFILE_CHANGED=true
    pass "Added Python to shell profile"
else
    pass "Shell profile already has Python PATH"
fi

# Ensure Homebrew is in PATH (Apple Silicon)
if [ -f "/opt/homebrew/bin/brew" ]; then
    if ! grep -q 'opt/homebrew' "$SHELL_CONFIG" 2>/dev/null; then
        cat >> "$SHELL_CONFIG" << 'BREW_EOF'

# Homebrew (Apple Silicon)
eval "$(/opt/homebrew/bin/brew shellenv)"
BREW_EOF
        PROFILE_CHANGED=true
        pass "Added Homebrew to shell profile"
    fi
fi

if [ "$PROFILE_CHANGED" = true ]; then
    warn "Shell profile was updated -- close and reopen Terminal after this script."
fi

# Make sure this session has the right PATH
export PATH="${PYTHON_BIN}:$PATH"

# ===============================================
# Step 2: Virtual environment
# ===============================================
echo ""
echo "--- Step 2: Virtual environment (.venv) ---"

VENV_OK=false
if [ -d ".venv" ] && [ -x ".venv/bin/python3" ]; then
    VENV_PY=$(.venv/bin/python3 --version 2>&1)
    if [[ "$VENV_PY" == *"$PYTHON_MAJOR"* ]]; then
        VENV_OK=true
        pass ".venv exists ($VENV_PY)"
    else
        warn ".venv has wrong Python ($VENV_PY) -- rebuilding..."
        rm -rf .venv
    fi
fi

if [ "$VENV_OK" = false ]; then
    if [ -d ".venv" ]; then
        info "Removing broken .venv..."
        rm -rf .venv
    fi
    info "Creating .venv with Python $PYTHON_MAJOR..."
    "${PYTHON_BIN}/python3" -m venv .venv
    pass ".venv created"
fi

# ===============================================
# Step 3: Install requirements
# ===============================================
echo ""
echo "--- Step 3: Requirements ---"

info "Updating pip..."
.venv/bin/pip install --upgrade pip > /dev/null 2>&1

info "Installing packages from requirements.txt..."
if .venv/bin/pip install -r requirements.txt 2>&1 | tail -1; then
    echo ""
    # Verify each package from requirements.txt
    ALL_OK=true
    while IFS= read -r line; do
        # Skip blank lines and comments
        [[ -z "$line" || "$line" == \#* ]] && continue
        # Extract package name (strip version specifiers)
        pkg=$(echo "$line" | sed 's/[>=<!\[].*//; s/-/_/g')
        if .venv/bin/pip show "$pkg" > /dev/null 2>&1; then
            installed_ver=$(.venv/bin/pip show "$pkg" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
            pass "$pkg ($installed_ver)"
        else
            fail "$pkg -- NOT installed"
            ALL_OK=false
        fi
    done < "$PROJECT_DIR/requirements.txt"

    if [ "$ALL_OK" = false ]; then
        warn "Some packages failed. Try running manually:"
        echo "       source .venv/bin/activate"
        echo "       pip install -r requirements.txt"
    fi
else
    fail "pip install failed"
    echo "       Try: source .venv/bin/activate && pip install -r requirements.txt"
fi

# ===============================================
# Step 4: RoboRIO deploy prep
# ===============================================
echo ""
echo "--- Step 4: Robot deploy prep ---"

mkdir -p "$HOME/wpilib/2026/robotpy/pip_cache"
pass "pip_cache directory ready"

info "Downloading RoboRIO Python (OK to skip if offline)..."
if .venv/bin/python -m robotpy installer download-python 2>/dev/null; then
    pass "RoboRIO Python downloaded"
else
    warn "Could not download (offline?). Run later when connected:"
    echo "       python -m robotpy installer download-python"
fi

info "Downloading RoboRIO packages..."
if .venv/bin/python -m robotpy installer download -r requirements.txt 2>/dev/null; then
    pass "RoboRIO packages downloaded"
else
    warn "Could not download (offline?). Run later when connected:"
    echo "       python -m robotpy installer download -r requirements.txt"
fi

# ===============================================
# Step 5: Git identity
# ===============================================
echo ""
echo "--- Step 5: Git ---"

if git config user.name &> /dev/null && git config user.email &> /dev/null; then
    pass "Git user: $(git config user.name) <$(git config user.email)>"
else
    echo ""
    echo "  Git needs your name and email for commits."
    echo ""
    if ! git config user.name &> /dev/null; then
        read -p "  Your name (e.g. Caleb): " GIT_NAME
        if [ -n "$GIT_NAME" ]; then
            git config --global user.name "$GIT_NAME"
            pass "Git name set to: $GIT_NAME"
        fi
    fi
    if ! git config user.email &> /dev/null; then
        read -p "  Your email: " GIT_EMAIL
        if [ -n "$GIT_EMAIL" ]; then
            git config --global user.email "$GIT_EMAIL"
            pass "Git email set to: $GIT_EMAIL"
        fi
    fi
fi

# GitHub auth check
if command -v gh &> /dev/null; then
    if gh auth status &> /dev/null 2>&1; then
        pass "GitHub CLI is logged in"
    else
        warn "GitHub CLI is NOT logged in (can't push/pull)"
        echo ""
        echo "  Run this now or after the script finishes:"
        echo "    gh auth login"
        echo "  (Choose: GitHub.com, HTTPS, Login with a web browser)"
    fi
else
    fail "GitHub CLI (gh) not installed on this Mac"
    echo "       Ask Brian to run: ./team -> option 6"
fi

# ===============================================
# Done!
# ===============================================
echo ""
echo "========================================"
echo -e " ${GREEN}Project setup complete!${NC}"
echo "========================================"
echo ""
echo "Every time you open a terminal to work:"
echo ""
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  git pull"
echo ""
echo "Run ./team anytime for the full menu, or option 1 for a quick checkup."
echo ""
