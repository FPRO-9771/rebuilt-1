#
# Team 9771 FPRO - Team CLI (Windows PowerShell)
# Entry point. Run from the project root with:  .\team.ps1
#
# If you get a "running scripts is disabled" error, run this once:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#

$ErrorActionPreference = "Stop"
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# -----------------------------------------------
# Colors / output helpers
# -----------------------------------------------
function Write-Pass($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  [!!] $msg" -ForegroundColor Red }
function Write-Warn($msg) { Write-Host "  [??] $msg" -ForegroundColor Yellow }
function Write-Info($msg) { Write-Host "  [..] $msg" -ForegroundColor Cyan }
function Write-Fix($msg)  { Write-Host "       Fix: $msg" }

function Show-Header {
    Clear-Host
    Write-Host ""
    Write-Host "========================================" -ForegroundColor White
    Write-Host " Team 9771 FPRO" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor White
    Write-Host ""
}

function Read-Choice($prompt) {
    Write-Host ""
    Write-Host -NoNewline "  > "
    return (Read-Host).Trim().ToLower()
}

function Pause-Continue {
    Write-Host ""
    Write-Host -NoNewline "Press Enter to continue..."
    Read-Host | Out-Null
}

# -----------------------------------------------
# Run a command with a header, pause when done
# -----------------------------------------------
function Invoke-TeamCommand($desc, [scriptblock]$cmd) {
    Show-Header
    Write-Host "--- $desc ---" -ForegroundColor White
    Write-Host ""
    try {
        & $cmd
        Write-Host ""
        Write-Host "Done." -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "Finished with errors: $_" -ForegroundColor Yellow
    }
    Pause-Continue
}

# -----------------------------------------------
# Run a command inside .venv
# -----------------------------------------------
function Invoke-InVenv($desc, [scriptblock]$cmd) {
    $venvPy = Join-Path $PROJECT_DIR ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPy)) {
        Show-Header
        Write-Host ""
        Write-Fail ".venv is not set up yet."
        Write-Host ""
        Write-Host "  Run option 2 (Set up my account) first." -ForegroundColor Yellow
        Write-Host ""
        Pause-Continue
        return
    }

    Show-Header
    Write-Host "--- $desc ---" -ForegroundColor White
    Write-Host ""

    # Activate venv for this block
    $activateScript = Join-Path $PROJECT_DIR ".venv\Scripts\Activate.ps1"
    & $activateScript

    Set-Location $PROJECT_DIR

    try {
        & $cmd
        Write-Host ""
        Write-Host "Done." -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "Finished with warnings: $_" -ForegroundColor Yellow
    }

    deactivate 2>$null
    Pause-Continue
}

# -----------------------------------------------
# COMMAND: Check environment
# -----------------------------------------------
function Invoke-CheckEnv {
    Show-Header
    Write-Host "--- Environment Check ---" -ForegroundColor White
    Write-Host ""

    $PYTHON_MAJOR = "3.13"
    $problems = 0
    $warnings = 0

    # --- System tools ---
    Write-Host "=== System Tools ===" -ForegroundColor White
    Write-Host ""

    # Python
    try {
        $pyVer = & python --version 2>&1
        if ($pyVer -like "*$PYTHON_MAJOR*") {
            Write-Pass "Python $PYTHON_MAJOR -- $pyVer"
        } else {
            Write-Fail "python is $pyVer (need $PYTHON_MAJOR)"
            Write-Fix "Run cli\commands\setup_windows.ps1 as Administrator"
            $problems++
        }
    } catch {
        Write-Fail "python not found"
        Write-Fix "Run cli\commands\setup_windows.ps1 as Administrator"
        $problems++
    }

    # GitHub CLI
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        Write-Pass "GitHub CLI (gh) installed"
    } else {
        Write-Fail "GitHub CLI (gh) not found"
        Write-Fix "Download from: https://cli.github.com"
        $problems++
    }

    # Claude Code
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        Write-Pass "Claude Code installed"
    } else {
        Write-Fail "Claude Code not found"
        Write-Fix "npm install -g @anthropic-ai/claude-code"
        $problems++
    }

    # Node.js
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nodeVer = & node --version 2>&1
        Write-Pass "Node.js -- $nodeVer"
    } else {
        Write-Fail "Node.js not found"
        Write-Fix "Download from: https://nodejs.org"
        $problems++
    }

    # --- Your account ---
    Write-Host ""
    Write-Host "=== Your Account ===" -ForegroundColor White
    Write-Host ""

    # GitHub auth
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        $ghStatus = & gh auth status 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "GitHub logged in"
        } else {
            Write-Fail "GitHub NOT logged in (can't push/pull)"
            Write-Fix "Run: gh auth login"
            $problems++
        }
    }

    # Git identity
    try {
        $gitName = & git config user.name 2>&1
        $gitEmail = & git config user.email 2>&1
        if ($gitName -and $gitEmail) {
            Write-Pass "Git user: $gitName"
        } else {
            Write-Fail "Git name/email not set"
            Write-Fix "Run option 2 (Set up my account)"
            $problems++
        }
    } catch {
        Write-Fail "Git not found or not configured"
        $problems++
    }

    # --- Project ---
    Write-Host ""
    Write-Host "=== Project ===" -ForegroundColor White
    Write-Host ""

    Set-Location $PROJECT_DIR

    $venvPy = Join-Path $PROJECT_DIR ".venv\Scripts\python.exe"
    $venvGood = $false
    if (Test-Path $venvPy) {
        $venvVer = & $venvPy --version 2>&1
        if ($venvVer -like "*$PYTHON_MAJOR*") {
            Write-Pass ".venv -- $venvVer"
            $venvGood = $true
        } else {
            Write-Fail ".venv has wrong Python ($venvVer, need $PYTHON_MAJOR)"
            Write-Fix "Run option 2 (Set up my account)"
            $problems++
        }
    } else {
        Write-Fail ".venv missing or broken"
        Write-Fix "Run option 2 (Set up my account)"
        $problems++
    }

    if ($venvGood) {
        $venvPip = Join-Path $PROJECT_DIR ".venv\Scripts\pip.exe"
        $reqFile = Join-Path $PROJECT_DIR "requirements.txt"
        $missing = 0
        foreach ($line in Get-Content $reqFile) {
            $line = $line.Trim()
            if ($line -eq "" -or $line.StartsWith("#")) { continue }
            $pkg = ($line -replace '[>=<![].*', '').Trim() -replace '-', '_'
            $showResult = & $venvPip show $pkg 2>&1
            if ($LASTEXITCODE -eq 0) {
                $ver = ($showResult | Select-String "^Version:").ToString() -replace "Version: ", ""
                Write-Pass "$pkg ($ver)"
            } else {
                Write-Fail "$pkg -- NOT installed"
                $missing++
            }
        }
        if ($missing -gt 0) {
            Write-Fix ".venv\Scripts\pip install -r requirements.txt"
            $problems++
        }
    }

    # --- Robot deploy ---
    Write-Host ""
    Write-Host "=== Robot Deploy ===" -ForegroundColor White
    Write-Host ""

    $pipCache = Join-Path $env:USERPROFILE "wpilib\2026\robotpy\pip_cache"
    if (Test-Path $pipCache) {
        $whlCount = (Get-ChildItem $pipCache -Filter "*.whl" -ErrorAction SilentlyContinue).Count
        if ($whlCount -gt 0) {
            Write-Pass "RoboRIO packages downloaded ($whlCount files in cache)"
        } else {
            Write-Warn "pip_cache exists but no .whl files (packages not downloaded yet)"
            Write-Fix "Run option 4 (Robot) -> option 5 (Download packages)"
            $warnings++
        }
    } else {
        Write-Warn "pip_cache not found (can't deploy without it)"
        Write-Fix "Run option 4 (Robot) -> option 5 (Download packages)"
        $warnings++
    }

    # --- Summary ---
    Write-Host ""
    Write-Host "========================================"
    if ($problems -eq 0 -and $warnings -eq 0) {
        Write-Host " ALL CLEAR -- ready to code!" -ForegroundColor Green
        Write-Host "========================================"
        Write-Host ""
        Write-Host "  .venv\Scripts\Activate.ps1   (activate venv)"
        Write-Host "  git pull                      (get latest code)"
        Write-Host "  python -m pytest tests/ -v    (run tests)"
        Write-Host "  python -m robotpy deploy      (deploy to robot)"
    } elseif ($problems -eq 0) {
        Write-Host " $warnings warning(s) -- mostly ready, check [??] above" -ForegroundColor Yellow
        Write-Host "========================================"
    } else {
        Write-Host " $problems problem(s) found!" -ForegroundColor Red
        if ($warnings -gt 0) { Write-Host " Plus $warnings warning(s)" -ForegroundColor Yellow }
        Write-Host "========================================"
    }
    Write-Host ""

    Pause-Continue
}

# -----------------------------------------------
# COMMAND: Set up my account
# -----------------------------------------------
function Invoke-SetupProject {
    Show-Header
    Write-Host "--- Project Setup ---" -ForegroundColor White
    Write-Host ""

    $PYTHON_MAJOR = "3.13"
    Set-Location $PROJECT_DIR

    # Step 1: Check Python
    Write-Host "--- Step 1: Python ---"
    try {
        $pyVer = & python --version 2>&1
        if ($pyVer -like "*$PYTHON_MAJOR*") {
            Write-Pass "Python $PYTHON_MAJOR found -- $pyVer"
        } else {
            Write-Fail "python is $pyVer (need $PYTHON_MAJOR)"
            Write-Host ""
            Write-Host "  Run cli\commands\setup_windows.ps1 as Administrator first." -ForegroundColor Yellow
            Write-Host ""
            Pause-Continue
            return
        }
    } catch {
        Write-Fail "python not found -- run cli\commands\setup_windows.ps1 as Administrator first"
        Write-Host ""
        Pause-Continue
        return
    }

    # Step 2: Virtual environment
    Write-Host ""
    Write-Host "--- Step 2: Virtual environment (.venv) ---"
    $venvPy = Join-Path $PROJECT_DIR ".venv\Scripts\python.exe"
    $venvOk = $false

    if (Test-Path $venvPy) {
        $venvVer = & $venvPy --version 2>&1
        if ($venvVer -like "*$PYTHON_MAJOR*") {
            $venvOk = $true
            Write-Pass ".venv exists ($venvVer)"
        } else {
            Write-Warn ".venv has wrong Python ($venvVer) -- rebuilding..."
            Remove-Item -Path (Join-Path $PROJECT_DIR ".venv") -Recurse -Force
        }
    }

    if (-not $venvOk) {
        Write-Info "Creating .venv with Python $PYTHON_MAJOR..."
        & python -m venv .venv
        Write-Pass ".venv created"
    }

    # Step 3: Install requirements
    Write-Host ""
    Write-Host "--- Step 3: Requirements ---"
    $venvPip = Join-Path $PROJECT_DIR ".venv\Scripts\pip.exe"

    Write-Info "Updating pip..."
    & $venvPip install --upgrade pip 2>&1 | Out-Null

    Write-Info "Installing packages from requirements.txt..."
    & $venvPip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "All packages installed"
    } else {
        Write-Fail "Some packages failed -- try running manually:"
        Write-Host "       .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    }

    # Step 4: Robot deploy prep
    Write-Host ""
    Write-Host "--- Step 4: Robot deploy prep ---"
    $pipCache = Join-Path $env:USERPROFILE "wpilib\2026\robotpy\pip_cache"
    New-Item -ItemType Directory -Force -Path $pipCache | Out-Null
    Write-Pass "pip_cache directory ready"

    $venvPython = Join-Path $PROJECT_DIR ".venv\Scripts\python.exe"
    Write-Info "Downloading RoboRIO Python (OK to skip if offline)..."
    & $venvPython -m robotpy installer download-python 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "RoboRIO Python downloaded"
    } else {
        Write-Warn "Could not download (offline?). Run later when connected:"
        Write-Host "       python -m robotpy installer download-python" -ForegroundColor Yellow
    }

    Write-Info "Downloading RoboRIO packages..."
    & $venvPython -m robotpy installer download -r requirements.txt 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "RoboRIO packages downloaded"
    } else {
        Write-Warn "Could not download (offline?). Run later when connected:"
        Write-Host "       python -m robotpy installer download -r requirements.txt" -ForegroundColor Yellow
    }

    # Step 5: Git identity
    Write-Host ""
    Write-Host "--- Step 5: Git ---"
    try {
        $gitName = & git config user.name 2>&1
        $gitEmail = & git config user.email 2>&1
        if ($gitName -and $gitEmail) {
            Write-Pass "Git user: $gitName <$gitEmail>"
        } else {
            throw "not configured"
        }
    } catch {
        Write-Host ""
        Write-Host "  Git needs your name and email for commits." -ForegroundColor Yellow
        Write-Host ""
        Write-Host -NoNewline "  Your name (e.g. Caleb): "
        $gitName = Read-Host
        if ($gitName) {
            & git config --global user.name $gitName
            Write-Pass "Git name set to: $gitName"
        }
        Write-Host -NoNewline "  Your email: "
        $gitEmail = Read-Host
        if ($gitEmail) {
            & git config --global user.email $gitEmail
            Write-Pass "Git email set to: $gitEmail"
        }
    }

    # GitHub auth check
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        & gh auth status 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "GitHub CLI is logged in"
        } else {
            Write-Warn "GitHub CLI is NOT logged in (can't push/pull)"
            Write-Host ""
            Write-Host "  Run this now or after the script:" -ForegroundColor Yellow
            Write-Host "    gh auth login" -ForegroundColor Yellow
            Write-Host "  (Choose: GitHub.com, HTTPS, Login with a web browser)" -ForegroundColor Yellow
        }
    } else {
        Write-Fail "GitHub CLI (gh) not installed -- download from https://cli.github.com"
    }

    Write-Host ""
    Write-Host "========================================"
    Write-Host " Project setup complete!" -ForegroundColor Green
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Every time you open a terminal to work:"
    Write-Host ""
    Write-Host "  cd $PROJECT_DIR"
    Write-Host "  .venv\Scripts\Activate.ps1"
    Write-Host "  git pull"
    Write-Host ""
    Write-Host "Run .\team.ps1 anytime for the full menu."
    Write-Host ""

    Pause-Continue
}

# -----------------------------------------------
# COMMAND: Git push (with commit message prompt)
# -----------------------------------------------
function Invoke-GitPush {
    Show-Header
    Write-Host "--- Save and Push ---" -ForegroundColor White
    Write-Host ""

    Set-Location $PROJECT_DIR
    & git status --short

    # Check if anything to commit
    $diff = & git diff --quiet 2>&1; $d1 = $LASTEXITCODE
    $diffCached = & git diff --cached --quiet 2>&1; $d2 = $LASTEXITCODE
    $untracked = & git ls-files --others --exclude-standard 2>&1
    if ($d1 -eq 0 -and $d2 -eq 0 -and -not $untracked) {
        Write-Host ""
        Write-Host "Nothing to save -- your code matches the last commit." -ForegroundColor Yellow
        Write-Host ""
        Pause-Continue
        return
    }

    Write-Host ""
    Write-Host -NoNewline "  Commit message (what did you change?): "
    $msg = Read-Host

    if (-not $msg) {
        Write-Host ""
        Write-Host "  No message entered. Cancelled." -ForegroundColor Yellow
        Write-Host ""
        Pause-Continue
        return
    }

    Write-Host ""
    & git add -A
    & git commit -m $msg
    & git push

    Write-Host ""
    Write-Host "Done! Your changes are saved and pushed." -ForegroundColor Green
    Write-Host ""
    Pause-Continue
}

# -----------------------------------------------
# COMMAND: Git undo
# -----------------------------------------------
function Invoke-GitUndo {
    Show-Header
    Write-Host "--- Undo All Changes ---" -ForegroundColor White
    Write-Host ""
    Write-Host "This will throw away ALL changes you haven't committed." -ForegroundColor Yellow
    Write-Host ""

    Set-Location $PROJECT_DIR
    & git status --short

    Write-Host ""
    Write-Host -NoNewline "  Are you sure you want to undo everything? (y/n) > "
    $answer = Read-Host
    if ($answer -match '^[Yy]') {
        & git checkout -- .
        & git clean -fd
        Write-Host ""
        Write-Host "All changes undone. Code matches the last commit." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Cancelled." -ForegroundColor Yellow
    }

    Write-Host ""
    Pause-Continue
}

# -----------------------------------------------
# MENU: Code (git)
# -----------------------------------------------
function Show-CodeMenu {
    while ($true) {
        Show-Header
        Write-Host " Code (Git)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1) Get latest code"
        Write-Host "  2) Save and push my changes"
        Write-Host "  3) See what I've changed"
        Write-Host "  4) Undo ALL my changes (careful!)"
        Write-Host ""
        Write-Host "  b) Back" -ForegroundColor DarkGray
        $choice = Read-Choice ""

        switch ($choice) {
            "1" { Invoke-TeamCommand "Git Pull" { git -C $PROJECT_DIR pull } }
            "2" { Invoke-GitPush }
            "3" { Invoke-TeamCommand "Git Status" { git -C $PROJECT_DIR status } }
            "4" { Invoke-GitUndo }
            "b" { return }
        }
    }
}

# -----------------------------------------------
# MENU: Robot
# -----------------------------------------------
function Show-RobotMenu {
    while ($true) {
        Show-Header
        Write-Host " Robot" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1) Run tests"
        Write-Host "  2) Run simulation"
        Write-Host ""
        Write-Host "  3) Deploy to robot"
        Write-Host "  4) Deploy to robot (skip tests)"
        Write-Host ""
        Write-Host "  5) Download packages for robot"
        Write-Host "  6) Install packages on robot"
        Write-Host ""
        Write-Host "  b) Back" -ForegroundColor DarkGray
        $choice = Read-Choice ""

        switch ($choice) {
            "1" { Invoke-InVenv "Running Tests"            { python -m pytest tests/ -v } }
            "2" { Invoke-InVenv "Running Simulation"       { python -m robotpy sim } }
            "3" { Invoke-InVenv "Deploying to Robot"       { python -m robotpy deploy } }
            "4" { Invoke-InVenv "Deploying to Robot"       { python -m robotpy deploy --skip-tests } }
            "5" {
                Invoke-InVenv "Downloading Robot Packages" {
                    Write-Host "Downloading Python for RoboRIO..."
                    python -m robotpy installer download-python
                    Write-Host ""
                    Write-Host "Downloading project packages for RoboRIO..."
                    python -m robotpy installer download -r requirements.txt
                }
            }
            "6" {
                Invoke-InVenv "Installing Packages on Robot" {
                    Write-Host "Make sure you are connected to the robot (USB or network)."
                    Write-Host ""
                    Write-Host "Installing packages on RoboRIO..."
                    python -m robotpy installer install -r requirements.txt
                }
            }
            "b" { return }
        }
    }
}

# -----------------------------------------------
# MENU: Main
# -----------------------------------------------
function Show-MainMenu {
    while ($true) {
        Show-Header
        Write-Host " What do you want to do?" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1) Check my environment"
        Write-Host "  2) Set up my account (first time on this Windows PC)"
        Write-Host ""
        Write-Host "  3) Code (git pull, push, status) ..."
        Write-Host "  4) Robot (test, simulate, deploy) ..."
        Write-Host ""
        Write-Host "  5) Open Claude Code"
        Write-Host "  6) Windows setup  -->  run cli\commands\setup_windows.ps1 as Admin"
        Write-Host ""
        Write-Host "  q) Quit" -ForegroundColor DarkGray
        $choice = Read-Choice ""

        switch ($choice) {
            "1" { Invoke-CheckEnv }
            "2" { Invoke-SetupProject }
            "3" { Show-CodeMenu }
            "4" { Show-RobotMenu }
            "5" { Invoke-TeamCommand "Claude Code" { claude } }
            "6" {
                Show-Header
                Write-Host "  To do Windows setup, open PowerShell as Administrator and run:" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "    .\cli\commands\setup_windows.ps1" -ForegroundColor White
                Write-Host ""
                Pause-Continue
            }
            "q" { Clear-Host; Write-Host ""; Write-Host "Bye!"; Write-Host ""; exit 0 }
        }
    }
}

# --- Go ---
Show-MainMenu
