#!/bin/bash
#
# Main menu
#

menu_main() {
    while true; do
        show_menu "What do you want to do?" \
            "1|Check my environment|./cli/commands/check_env.sh" \
            "2|Set up my account (first time on this Mac)|./cli/commands/setup_project.sh" \
            "---|" \
            "3|Code (git pull, push, status) ..." \
            "4|Robot (test, simulate, deploy) ..." \
            "---|" \
            "5|Open Claude Code|claude" \
            "6|Mac setup (needs admin user's credentials)|./cli/commands/setup_mac.sh" \
            "q|Quit"

        case "$MENU_CHOICE" in
            1) run_command "Environment Check" "$CLI_DIR/commands/check_env.sh" ;;
            2) run_command "Project Setup" "$CLI_DIR/commands/setup_project.sh" ;;
            3) menu_code ;;
            4) menu_robot ;;
            5) run_command "Claude Code" claude ;;
            6) run_command "Mac Setup (admin)" "$CLI_DIR/commands/setup_mac.sh" ;;
            q) clear; echo ""; echo "Bye!"; echo ""; exit 0 ;;
            *) ;; # invalid input, just redraw
        esac
    done
}
