#!/bin/bash
#
# Team 9771 FPRO - Environment Check
# Quick diagnostic -- any team member can run this, no admin needed.
# Takes about 2 seconds. Shows green/red for everything you need.
#
# Usage:  ./team  (option 1)   -or-   ./cli/commands/check_env.sh
#

PYTHON_MAJOR="3.13"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/${PYTHON_MAJOR}/bin"

# Project root is two levels up from cli/commands/
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}[OK]${NC} $1"; }
fail() { echo -e "  ${RED}[!!]${NC} $1"; PROBLEMS=$((PROBLEMS + 1)); }
warn() { echo -e "  ${YELLOW}[??]${NC} $1"; WARNINGS=$((WARNINGS + 1)); }
fix()  { echo -e "       Fix: $1"; }

PROBLEMS=0
WARNINGS=0

echo ""
echo "========================================"
echo " Team 9771 FPRO - Environment Check"
echo "========================================"

# ==============================================================
# PART 1: Mac tools (system-wide -- need Brian for fixes)
# ==============================================================
echo ""
echo -e "${BOLD}=== Mac Tools ===${NC}  (if broken, ask Brian to run setup_mac.sh)"
echo ""

# -- Python --
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version 2>&1)
    if [[ "$PY_VER" == *"$PYTHON_MAJOR"* ]]; then
        pass "Python $PYTHON_MAJOR -- $PY_VER"
    else
        fail "python3 is $PY_VER (need $PYTHON_MAJOR)"
    fi
else
    fail "python3 not found"
fi

# -- Conflicting Pythons --
BAD_PYTHONS=""
for version in 3.8 3.9 3.10 3.11 3.12 3.14; do
    if [ -d "/Library/Frameworks/Python.framework/Versions/$version" ]; then
        BAD_PYTHONS="$BAD_PYTHONS $version"
    fi
done
if [ -n "$BAD_PYTHONS" ]; then
    warn "Old Python versions still installed:$BAD_PYTHONS"
else
    pass "No conflicting Python versions"
fi

# -- Node.js --
if command -v node &> /dev/null; then
    pass "Node.js -- $(node --version)"
else
    fail "Node.js not found"
fi

# -- GitHub CLI --
if command -v gh &> /dev/null; then
    pass "GitHub CLI (gh) installed"
else
    fail "GitHub CLI (gh) not found"
fi

# -- Claude Code --
if command -v claude &> /dev/null; then
    pass "Claude Code installed"
else
    fail "Claude Code not found"
fi

# ==============================================================
# PART 2: Your account (per-user -- you can fix these yourself)
# ==============================================================
echo ""
echo -e "${BOLD}=== Your Account ===${NC}  (fix with: ./team -> option 2)"
echo ""

# -- GitHub auth --
if command -v gh &> /dev/null; then
    if gh auth status &> /dev/null 2>&1; then
        GH_USER=$(gh auth status 2>&1 | grep "account" | head -1 | sed 's/.*account //' | sed 's/ .*//')
        pass "GitHub logged in${GH_USER:+ ($GH_USER)}"
    else
        fail "GitHub NOT logged in (can't push/pull)"
        fix "Run: gh auth login"
    fi
fi

# -- Git identity --
if git config user.name &> /dev/null && git config user.email &> /dev/null; then
    pass "Git user: $(git config user.name)"
else
    fail "Git name/email not set (commits won't work)"
    fix "Run: ./team -> option 2 (it will ask your name)"
fi

# -- Shell profile --
SHELL_CONFIG="$HOME/.zprofile"
[ ! -f "$SHELL_CONFIG" ] && SHELL_CONFIG="$HOME/.bash_profile"
if [ -f "$SHELL_CONFIG" ] && grep -q "Python.framework.*${PYTHON_MAJOR}" "$SHELL_CONFIG" 2>/dev/null; then
    pass "Shell profile has Python PATH"
else
    warn "Shell profile missing Python PATH (may cause issues in new terminals)"
    fix "Run: ./team -> option 2"
fi

# ==============================================================
# PART 3: Project / robot readiness
# ==============================================================
echo ""
echo -e "${BOLD}=== Project ===${NC}  (fix with: ./team -> option 2)"
echo ""

cd "$PROJECT_DIR"

# -- .venv existence and Python version --
VENV_GOOD=false
if [ -d ".venv" ] && [ -x ".venv/bin/python3" ]; then
    VENV_PY=$(.venv/bin/python3 --version 2>&1)
    if [[ "$VENV_PY" == *"$PYTHON_MAJOR"* ]]; then
        pass ".venv -- $VENV_PY"
        VENV_GOOD=true
    else
        fail ".venv has wrong Python ($VENV_PY, need $PYTHON_MAJOR)"
        fix "Run: ./team -> option 2"
    fi
else
    fail ".venv missing or broken"
    fix "Run: ./team -> option 2"
fi

# -- .venv activated --
if [ -n "$VIRTUAL_ENV" ]; then
    if [[ "$VIRTUAL_ENV" == *"$(basename "$PROJECT_DIR")"* ]]; then
        pass ".venv is activated"
    else
        warn "Wrong venv activated: $VIRTUAL_ENV"
        fix "Run: deactivate && source .venv/bin/activate"
    fi
else
    warn ".venv is NOT activated in this terminal"
    fix "Run: source .venv/bin/activate"
fi

# -- Check each package from requirements.txt --
if [ "$VENV_GOOD" = true ]; then
    REQ_MISSING=0
    while IFS= read -r line; do
        # Skip blank lines and comments
        [[ -z "$line" || "$line" == \#* ]] && continue
        # Extract package name (strip version specifiers like >=, ==, etc.)
        pkg=$(echo "$line" | sed 's/[>=<!\[].*//' | xargs)
        [ -z "$pkg" ] && continue
        # pip uses underscores internally
        pkg_normalized=$(echo "$pkg" | sed 's/-/_/g')
        if .venv/bin/pip show "$pkg_normalized" > /dev/null 2>&1; then
            installed_ver=$(.venv/bin/pip show "$pkg_normalized" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
            pass "$pkg ($installed_ver)"
        else
            fail "$pkg -- NOT installed"
            REQ_MISSING=$((REQ_MISSING + 1))
        fi
    done < "$PROJECT_DIR/requirements.txt"

    if [ "$REQ_MISSING" -gt 0 ]; then
        fix "Run: source .venv/bin/activate && pip install -r requirements.txt"
    fi
fi

# -- Deploy readiness --
echo ""
echo -e "${BOLD}=== Robot Deploy ===${NC}  (fix with: ./team -> Robot -> option 5)"
echo ""

if [ -d "$HOME/wpilib/2026/robotpy/pip_cache" ]; then
    pass "pip_cache directory exists"
else
    # Auto-create it (no admin needed)
    mkdir -p "$HOME/wpilib/2026/robotpy/pip_cache" 2>/dev/null
    if [ -d "$HOME/wpilib/2026/robotpy/pip_cache" ]; then
        pass "pip_cache directory created (was missing)"
    else
        fail "pip_cache directory missing"
        fix "Run: mkdir -p ~/wpilib/2026/robotpy/pip_cache"
    fi
fi

# Check for downloaded roboRIO packages
if ls "$HOME/wpilib/2026/robotpy/pip_cache/"*.whl &> /dev/null 2>&1; then
    WHL_COUNT=$(ls "$HOME/wpilib/2026/robotpy/pip_cache/"*.whl 2>/dev/null | wc -l | xargs)
    pass "RoboRIO packages downloaded ($WHL_COUNT files in cache)"
else
    warn "RoboRIO packages not downloaded yet (can't deploy without them)"
    fix "Run: source .venv/bin/activate"
    fix "     python -m robotpy installer download-python"
    fix "     python -m robotpy installer download -r requirements.txt"
fi

# ==============================================================
# Summary
# ==============================================================
echo ""
echo "========================================"
if [ "$PROBLEMS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e " ${GREEN}${BOLD}ALL CLEAR -- ready to code!${NC}"
    echo "========================================"
    echo ""
    echo "  source .venv/bin/activate    (if not already)"
    echo "  git pull                     (get latest code)"
    echo "  python -m pytest tests/ -v   (run tests)"
    echo "  python -m robotpy deploy     (deploy to robot)"
elif [ "$PROBLEMS" -eq 0 ]; then
    echo -e " ${YELLOW}${BOLD}$WARNINGS warning(s) -- mostly ready, check [??] above${NC}"
    echo "========================================"
else
    echo -e " ${RED}${BOLD}$PROBLEMS problem(s) found!${NC}"
    [ "$WARNINGS" -gt 0 ] && echo -e " ${YELLOW}Plus $WARNINGS warning(s)${NC}"
    echo "========================================"
    echo ""
    echo "  Mac Tools broken?  --> Ask Brian to run: ./team -> option 6"
    echo "  Project broken?    --> Run: ./team -> option 2"
fi
echo ""
