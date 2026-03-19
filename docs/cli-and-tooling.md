# Team CLI and Tooling

The team CLI is an interactive menu that wraps common tasks -- environment setup, git, testing, and deploy -- so team members do not need to memorize terminal commands.

---

## Running the CLI

From the project root:

```bash
./cli/team.sh
```

This sources the shared library (`cli/lib.sh`), loads all menu files from `cli/menus/`, and launches the main menu.

---

## Menu Structure

### Main Menu (`cli/menus/main.sh`)

| Option | Action |
|--------|--------|
| 1 | Check my environment (runs `check_env.sh`) |
| 2 | Set up my account -- first-time project setup |
| 3 | Code (git) sub-menu |
| 4 | Robot (test, sim, deploy) sub-menu |
| 5 | Open Claude Code |
| 6 | Mac setup (needs admin credentials, runs `setup_mac.sh`) |
| q | Quit |

### Code Menu (`cli/menus/code.sh`)

Git operations for team members who are not comfortable with the terminal:

| Option | Action |
|--------|--------|
| 1 | `git pull` -- get latest code |
| 2 | Stage all, commit with a message prompt, push |
| 3 | `git status` -- see local changes |
| 4 | Undo ALL uncommitted changes (asks for confirmation) |

### Robot Menu (`cli/menus/robot.sh`)

All commands here activate `.venv` automatically via `run_in_venv`.

| Option | Action |
|--------|--------|
| 1 | Run tests (`pytest tests/ -v`) |
| 2 | Run simulation (`robotpy sim`) |
| 3 | Deploy to robot (`robotpy deploy`) |
| 4 | Deploy, skip tests (`robotpy deploy --skip-tests`) |
| 5 | Download RoboRIO packages (Python + requirements) |
| 6 | Install packages on robot |

---

## Commands

Scripts in `cli/commands/` are standalone -- they can be run directly or through the menu.

### check_env.sh

Quick diagnostic (no admin needed). Checks:
- Python version, conflicting Python installs
- Node.js, GitHub CLI, Claude Code
- GitHub auth, git identity, shell profile
- `.venv` existence and correct Python version
- All packages from `requirements.txt`
- RoboRIO deploy cache (`pip_cache`)

Prints a summary with `[OK]`, `[!!]` (problem), or `[??]` (warning) for each item.

### setup_mac.sh

System-wide setup that installs tools for ALL user accounts. Requires admin credentials. Run once per Mac. Installs:
- Python 3.13 (from python.org .pkg)
- Node.js
- GitHub CLI (`gh`)
- Claude Code (via npm)

Also removes old/conflicting Python versions and sets up system-wide PATH entries.

### setup_project.sh

Per-user project setup. No admin needed. Any team member can run this. It:
- Configures the shell profile (Python PATH)
- Creates `.venv` with the correct Python
- Installs all packages from `requirements.txt`
- Downloads RoboRIO packages for deploy
- Sets up git user name and email

### setup_windows.ps1

PowerShell script for Windows machines. Run as Administrator. Removes old Python versions, installs Python 3.13 globally, and configures PATH. Also checks for Visual Studio Build Tools (required by RobotPy on Windows).

---

## Shared Library: lib.sh

`cli/lib.sh` is sourced by the entry point and all menus. It provides:

- **Colors** -- exported variables (`$GREEN`, `$RED`, `$YELLOW`, `$BOLD`, `$NC`, etc.) for consistent output.
- **Project paths** -- `$CLI_DIR` and `$PROJECT_DIR` so scripts do not hardcode paths.
- **`show_menu TITLE OPTIONS...`** -- renders a numbered menu, reads user input into `$MENU_CHOICE`. Options use pipe-delimited format: `"key|label"` or `"key|label|hint"`. Special keys: `---` (separator), `b` (back), `q` (quit).
- **`run_command DESC CMD...`** -- clears the screen, prints a header, runs the command, shows pass/fail, and waits for Enter.
- **`run_in_venv DESC CMD...`** -- same as `run_command` but activates `.venv` first. Errors if `.venv` is missing.
- **`confirm PROMPT`** -- yes/no prompt. Returns 0 for yes, 1 for no.

---

## Adding New Menus or Commands

**New command:** Add a script to `cli/commands/`. It should be self-contained (set its own `PROJECT_DIR`, define its own color helpers if run standalone). Wire it into a menu's `case` block.

**New menu:** Create a file in `cli/menus/` with a function (e.g., `menu_debug()`). It will be auto-sourced by `team.sh` because the entry point loads all `cli/menus/*.sh` files. Add a menu option in `main.sh` (or another menu) that calls your function.

**Pattern to follow:**

```bash
# cli/menus/my_menu.sh
menu_my_menu() {
    while true; do
        show_menu "My Menu" \
            "1|Do something|hint text" \
            "b|Back"
        case "$MENU_CHOICE" in
            1) run_command "Doing something" echo "hello" ;;
            b) return ;;
            *) ;;
        esac
    done
}
```
