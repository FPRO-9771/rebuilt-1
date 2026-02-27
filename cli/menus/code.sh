#!/bin/bash
#
# Code (git) sub-menu
#

menu_code() {
    while true; do
        show_menu "Code (Git)" \
            "1|Get latest code|git pull" \
            "2|Save and push my changes|git add -A && git commit && git push" \
            "3|See what I've changed|git status" \
            "4|Undo ALL my changes (careful!)|git checkout -- ." \
            "b|Back"

        case "$MENU_CHOICE" in
            1)
                run_command "Git Pull" git -C "$PROJECT_DIR" pull
                ;;
            2)
                cmd_git_push
                ;;
            3)
                run_command "Git Status" git -C "$PROJECT_DIR" status
                ;;
            4)
                cmd_git_undo
                ;;
            b) return ;;
            *) ;;
        esac
    done
}

cmd_git_push() {
    clear
    echo ""
    echo -e "${BOLD}--- Save and Push ---${NC}"
    echo ""

    cd "$PROJECT_DIR"
    git status --short

    # Check if there's anything to commit
    if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
        echo ""
        echo "Nothing to save -- your code matches the last commit."
        echo ""
        read -rp "Press Enter to continue..."
        return
    fi

    echo ""
    read -rp "  Commit message (what did you change?): " msg

    if [ -z "$msg" ]; then
        echo ""
        echo "  No message entered. Cancelled."
        echo ""
        read -rp "Press Enter to continue..."
        return
    fi

    echo ""
    git add -A
    git commit -m "$msg"
    git push

    echo ""
    echo -e "${GREEN}Done! Your changes are saved and pushed.${NC}"
    echo ""
    read -rp "Press Enter to continue..."
}

cmd_git_undo() {
    clear
    echo ""
    echo -e "${BOLD}--- Undo All Changes ---${NC}"
    echo ""
    echo -e "${YELLOW}This will throw away ALL changes you haven't committed.${NC}"
    echo ""

    cd "$PROJECT_DIR"
    git status --short

    if confirm "Are you sure you want to undo everything?"; then
        git checkout -- .
        git clean -fd
        echo ""
        echo -e "${GREEN}All changes undone. Code matches the last commit.${NC}"
    else
        echo ""
        echo "Cancelled."
    fi

    echo ""
    read -rp "Press Enter to continue..."
}
