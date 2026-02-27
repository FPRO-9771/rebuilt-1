#!/bin/bash
#
# Team 9771 FPRO - Team CLI
# Entry point. Sources the library and all menus, then launches main menu.
#
# Usage:  ./team   (from project root)
#

CLI_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load shared library
source "$CLI_DIR/lib.sh"

# Load all menus
for menu_file in "$CLI_DIR/menus/"*.sh; do
    source "$menu_file"
done

# Go
menu_main
