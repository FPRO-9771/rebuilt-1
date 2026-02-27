#
# Team 9771 FPRO - Windows Python Setup Script
# Removes old Python versions and installs Python 3.13 globally
#
# Usage: Run PowerShell as Administrator, then:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\setup_windows.ps1
#

$ErrorActionPreference = "Stop"

$PYTHON_VERSION = "3.13.1"
$PYTHON_MAJOR = "3.13"
$INSTALLER_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
$INSTALLER_FILE = "$env:TEMP\python-$PYTHON_VERSION-amd64.exe"
$INSTALL_PATH = "C:\Python313"

Write-Host "========================================"
Write-Host "Team 9771 FPRO - Python Setup for Windows"
Write-Host "========================================"
Write-Host ""
Write-Host "This script will:"
Write-Host "  1. Remove old Python versions"
Write-Host "  2. Install Python $PYTHON_VERSION globally"
Write-Host "  3. Set up PATH for all users"
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Please run PowerShell as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "Steps:"
    Write-Host "  1. Press Windows key"
    Write-Host "  2. Type 'PowerShell'"
    Write-Host "  3. Right-click 'Windows PowerShell'"
    Write-Host "  4. Click 'Run as administrator'"
    Write-Host ""
    exit 1
}

Write-Host "Running as Administrator - OK"
Write-Host ""

# --- Step 1: Remove old Python versions ---
Write-Host "Step 1: Removing old Python versions..."
Write-Host ""

# Find and uninstall Python via Windows installer
$pythonApps = Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like "*Python*" }

foreach ($app in $pythonApps) {
    # Skip Python 3.13 if already installed
    if ($app.Name -like "*3.13*") {
        Write-Host "  Keeping: $($app.Name)"
        continue
    }

    Write-Host "  Uninstalling: $($app.Name)..."
    try {
        $app.Uninstall() | Out-Null
        Write-Host "    Removed."
    } catch {
        Write-Host "    Could not uninstall (may need manual removal)" -ForegroundColor Yellow
    }
}

# Remove Python from common installation directories
$pythonDirs = @(
    "C:\Python38",
    "C:\Python39",
    "C:\Python310",
    "C:\Python311",
    "C:\Python312",
    "C:\Python314",
    "$env:LOCALAPPDATA\Programs\Python\Python38",
    "$env:LOCALAPPDATA\Programs\Python\Python39",
    "$env:LOCALAPPDATA\Programs\Python\Python310",
    "$env:LOCALAPPDATA\Programs\Python\Python311",
    "$env:LOCALAPPDATA\Programs\Python\Python312",
    "$env:LOCALAPPDATA\Programs\Python\Python314"
)

foreach ($dir in $pythonDirs) {
    if (Test-Path $dir) {
        Write-Host "  Removing directory: $dir"
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Clean up PATH - remove old Python entries
Write-Host "  Cleaning PATH..."

$systemPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Remove old Python paths from system PATH
$newSystemPath = ($systemPath -split ";" | Where-Object {
    $_ -notmatch "Python3[0-9]" -and
    $_ -notmatch "Python\\Python3[0-9]" -and
    $_ -notmatch "Programs\\Python" -and
    $_ -ne ""
}) -join ";"

# Remove old Python paths from user PATH
$newUserPath = ($userPath -split ";" | Where-Object {
    $_ -notmatch "Python3[0-9]" -and
    $_ -notmatch "Python\\Python3[0-9]" -and
    $_ -notmatch "Programs\\Python" -and
    $_ -ne ""
}) -join ";"

[Environment]::SetEnvironmentVariable("Path", $newSystemPath, "Machine")
[Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")

Write-Host "  Old Python versions removed."
Write-Host ""

# --- Step 2: Download Python ---
Write-Host "Step 2: Downloading Python $PYTHON_VERSION..."
Write-Host "  URL: $INSTALLER_URL"
Write-Host ""

# Remove old installer if exists
if (Test-Path $INSTALLER_FILE) {
    Remove-Item $INSTALLER_FILE -Force
}

try {
    # Use TLS 1.2
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($INSTALLER_URL, $INSTALLER_FILE)

    Write-Host "  Download complete."
} catch {
    Write-Host "ERROR: Failed to download Python installer" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""

# --- Step 3: Install Python ---
Write-Host "Step 3: Installing Python $PYTHON_VERSION (this may take a few minutes)..."
Write-Host "  Install path: $INSTALL_PATH"
Write-Host ""

# Install Python silently with all options
# InstallAllUsers=1 - Install for all users
# PrependPath=1 - Add to PATH
# Include_test=0 - Skip test suite
# TargetDir - Install location

$installArgs = @(
    "/quiet",
    "InstallAllUsers=1",
    "PrependPath=1",
    "Include_test=0",
    "Include_pip=1",
    "Include_launcher=1",
    "TargetDir=$INSTALL_PATH"
)

try {
    $process = Start-Process -FilePath $INSTALLER_FILE -ArgumentList $installArgs -Wait -PassThru

    if ($process.ExitCode -ne 0) {
        Write-Host "ERROR: Python installation failed with exit code $($process.ExitCode)" -ForegroundColor Red
        exit 1
    }

    Write-Host "  Installation complete."
} catch {
    Write-Host "ERROR: Failed to run Python installer" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Clean up installer
Remove-Item $INSTALLER_FILE -Force -ErrorAction SilentlyContinue

Write-Host ""

# --- Step 4: Verify PATH is set correctly ---
Write-Host "Step 4: Verifying PATH configuration..."
Write-Host ""

# Refresh environment variables
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

# Check if Python paths are in system PATH
$systemPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

if ($systemPath -notlike "*$INSTALL_PATH*") {
    Write-Host "  Adding Python to system PATH..."
    $newPath = "$INSTALL_PATH;$INSTALL_PATH\Scripts;$systemPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
}

Write-Host "  PATH configured."
Write-Host ""

# --- Step 5: Verify installation ---
Write-Host "Step 5: Verifying installation..."
Write-Host ""

# Refresh PATH again
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

$pythonExe = "$INSTALL_PATH\python.exe"

if (Test-Path $pythonExe) {
    $installedVersion = & $pythonExe --version 2>&1
    Write-Host "  Installed: $installedVersion"

    if ($installedVersion -like "*$PYTHON_MAJOR*") {
        Write-Host "  SUCCESS!" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Version mismatch. Expected Python $PYTHON_MAJOR" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    exit 1
}

Write-Host ""

# --- Step 6: Check for Visual Studio Build Tools ---
Write-Host "Step 6: Checking Visual Studio Build Tools..."
Write-Host ""

$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$hasBuildTools = $false

if (Test-Path $vsWhere) {
    $vsInstalls = & $vsWhere -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json 2>$null | ConvertFrom-Json
    if ($vsInstalls) {
        $hasBuildTools = $true
    }
}

if ($hasBuildTools) {
    Write-Host "  Visual Studio Build Tools found - OK" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Visual Studio Build Tools not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  RobotPy requires Visual Studio Build Tools."
    Write-Host "  Please install manually:"
    Write-Host "    1. Go to: https://visualstudio.microsoft.com/downloads/"
    Write-Host "    2. Download 'Build Tools for Visual Studio 2022'"
    Write-Host "    3. Run installer and select 'Desktop development with C++'"
    Write-Host ""
}

Write-Host ""
Write-Host "========================================"
Write-Host "Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "IMPORTANT: Close this PowerShell window and open a new one."
Write-Host ""
Write-Host "Then verify with:"
Write-Host "  python --version"
Write-Host "  where python"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  cd C:\path\to\rebuilt-1"
Write-Host "  pip install -r requirements.txt"
Write-Host ""

if (-not $hasBuildTools) {
    Write-Host "REMINDER: Install Visual Studio Build Tools before installing RobotPy!" -ForegroundColor Yellow
    Write-Host ""
}
