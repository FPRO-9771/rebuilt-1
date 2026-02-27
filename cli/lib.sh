#!/bin/bash
#
# Team 9771 FPRO - CLI shared library
# Provides menu rendering, colors, and helpers.
# Sourced by the entry point and menu files -- not run directly.
#

# -----------------------------------------------
# Colors
# -----------------------------------------------
export GREEN='\033[0;32m'
export RED='\033[0;31m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export BOLD='\033[1m'
export DIM='\033[2m'
export NC='\033[0m'

# -----------------------------------------------
# Project paths
# -----------------------------------------------
export CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_DIR="$(cd "$CLI_DIR/.." && pwd)"

# -----------------------------------------------
# show_menu TITLE OPTION_LINES...
#
# Each OPTION_LINE is "key|label" or "key|label|command"
#   key     = what the user types (1, 2, a, b, etc.)
#   label   = what they see
#   command = bash code to eval (optional -- if omitted, returns the key)
#
# Special keys:
#   "---"  = separator line (label is the separator text)
#   "b"    = back (auto-styled)
#   "q"    = quit (auto-styled)
#
# Returns: the key the user picked (via MENU_CHOICE global)
# -----------------------------------------------
show_menu() {
    local title="$1"
    shift
    local options=("$@")

    clear
    echo ""
    echo -e "${BOLD}========================================"
    echo -e " Team 9771 FPRO"
    echo -e "========================================${NC}"
    echo ""
    echo -e " ${CYAN}${title}${NC}"
    echo ""

    # Render options
    # Format: "key|label" or "key|label|command hint"
    for opt in "${options[@]}"; do
        local key label hint
        key=$(echo "$opt" | cut -d'|' -f1)
        label=$(echo "$opt" | cut -d'|' -f2)
        hint=$(echo "$opt" | cut -d'|' -f3)

        if [ "$key" = "---" ]; then
            echo ""
            [ -n "$label" ] && echo -e " ${DIM}${label}${NC}"
        elif [ "$key" = "q" ]; then
            echo ""
            echo -e "  ${DIM}q)${NC} ${DIM}Quit${NC}"
        elif [ "$key" = "b" ]; then
            echo ""
            echo -e "  ${DIM}b)${NC} ${DIM}Back${NC}"
        elif [ -n "$hint" ]; then
            echo -e "  ${BOLD}${key})${NC} ${label}  ${DIM}${hint}${NC}"
        else
            echo -e "  ${BOLD}${key})${NC} ${label}"
        fi
    done

    echo ""
    echo -n "  > "
    read -r MENU_CHOICE
    MENU_CHOICE=$(echo "$MENU_CHOICE" | tr '[:upper:]' '[:lower:]' | xargs)
}

# -----------------------------------------------
# run_command DESCRIPTION COMMAND...
#
# Runs a command with a header, waits for Enter when done.
# -----------------------------------------------
run_command() {
    local desc="$1"
    shift

    clear
    echo ""
    echo -e "${BOLD}--- ${desc} ---${NC}"
    echo ""

    "$@"
    local exit_code=$?

    echo ""
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}Done.${NC}"
    else
        echo -e "${YELLOW}Finished with warnings (exit code $exit_code).${NC}"
    fi
    echo ""
    read -rp "Press Enter to continue..."
}

# -----------------------------------------------
# run_in_venv DESCRIPTION COMMAND...
#
# Activates .venv first, then runs the command.
# -----------------------------------------------
run_in_venv() {
    local desc="$1"
    shift

    if [ ! -x "$PROJECT_DIR/.venv/bin/python3" ]; then
        clear
        echo ""
        echo -e "${RED}[!!] .venv is not set up yet.${NC}"
        echo ""
        echo "  Run option 2 (Set up my account) first."
        echo ""
        read -rp "Press Enter to continue..."
        return 1
    fi

    clear
    echo ""
    echo -e "${BOLD}--- ${desc} ---${NC}"
    echo ""

    # Activate venv for this subshell
    source "$PROJECT_DIR/.venv/bin/activate"
    cd "$PROJECT_DIR"

    "$@"
    local exit_code=$?

    echo ""
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}Done.${NC}"
    else
        echo -e "${YELLOW}Finished with warnings (exit code $exit_code).${NC}"
    fi
    echo ""
    read -rp "Press Enter to continue..."
}

# -----------------------------------------------
# confirm PROMPT
#
# Returns 0 if user says yes, 1 if no.
# -----------------------------------------------
confirm() {
    echo ""
    read -rp "  $1 (y/n) > " answer
    [[ "$answer" =~ ^[Yy] ]]
}
