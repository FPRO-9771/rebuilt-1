# Python Setup Guide - Team 9771 FPRO

This guide will help you set up Python correctly for FRC robot development. **Follow these steps carefully** - having multiple Python versions causes problems.

## Required Version: Python 3.13

RobotPy 2026 supports Python 3.10-3.14. We use **Python 3.13** because:
- It's stable and well-tested
- Compatible with all our libraries
- Matches what most teams use

**Important:** You should have ONLY Python 3.13 installed. Multiple versions cause PATH confusion and errors.

---

## Mac Setup

### Option A: Run the Setup Script (Recommended)

We have a script that does everything for you:

```bash
# Open Terminal, navigate to the project folder, then run:
chmod +x scripts/setup_mac.sh
sudo ./scripts/setup_mac.sh
```

After the script finishes, **close and reopen Terminal**, then verify:
```bash
python3 --version
# Should show: Python 3.13.x
```

### Option B: Manual Setup

#### Step 1: Remove Old Python Versions

First, let's clean up any old Python installations:

```bash
# Check what Python versions you have
ls /Library/Frameworks/Python.framework/Versions/ 2>/dev/null
ls /usr/local/bin/python* 2>/dev/null

# Remove Homebrew Python (if installed)
brew uninstall python python@3.9 python@3.10 python@3.11 python@3.12 python@3.14 2>/dev/null

# Remove old python.org installations (run for each version you found above)
# Example for Python 3.11:
sudo rm -rf /Library/Frameworks/Python.framework/Versions/3.11
sudo rm -rf "/Applications/Python 3.11"
```

#### Step 2: Install Python 3.13

1. Go to: https://www.python.org/downloads/release/python-3131/
2. Download: **macOS 64-bit universal2 installer**
3. Run the installer
4. **Important:** Check the box for "Install for all users" if available
5. Complete the installation

#### Step 3: Set Up PATH

Add Python to your PATH so it works from any Terminal window:

```bash
# Open your shell profile
nano ~/.zprofile

# Add these lines at the end:
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
alias python=python3
alias pip=pip3

# Save: Ctrl+O, Enter, Ctrl+X
```

#### Step 4: Verify Installation

Close Terminal completely and reopen it, then run:

```bash
python3 --version
# Should show: Python 3.13.x

which python3
# Should show: /Library/Frameworks/Python.framework/Versions/3.13/bin/python3

pip3 --version
# Should show pip and Python 3.13
```

---

## Windows Setup

### Option A: Run the Setup Script (Recommended)

We have a PowerShell script that does everything for you:

1. Open **PowerShell as Administrator**:
   - Press Windows key
   - Type "PowerShell"
   - Right-click "Windows PowerShell"
   - Click "Run as administrator"

2. Navigate to the project and run the script:
```powershell
cd C:\path\to\rebuilt-1
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup_windows.ps1
```

After the script finishes, **close and reopen PowerShell**, then verify:
```powershell
python --version
# Should show: Python 3.13.x
```

### Option B: Manual Setup

#### Step 1: Remove Old Python Versions

1. Open **Settings** > **Apps** > **Installed apps**
2. Search for "Python"
3. Uninstall ALL Python versions you find (Python 3.9, 3.10, 3.11, 3.12, etc.)
4. Also uninstall any "Python Launcher" entries

Also remove from PATH:
1. Search for "Environment Variables" in Windows
2. Click "Edit the system environment variables"
3. Click "Environment Variables..."
4. In both User and System variables, find "Path" and edit it
5. Remove any entries containing "Python" or "python"

#### Step 2: Install Python 3.13

1. Go to: https://www.python.org/downloads/release/python-3131/
2. Download: **Windows installer (64-bit)**
3. Run the installer
4. **IMPORTANT:** Check these boxes:
   - [x] **Install for all users**
   - [x] **Add Python to PATH**
5. Click "Customize installation"
6. Check all Optional Features, click Next
7. Check:
   - [x] Install for all users
   - [x] Add Python to environment variables
   - [x] Precompile standard library
8. Install to: `C:\Python313` (simpler path, less issues)
9. Complete the installation

#### Step 3: Install Visual Studio Build Tools

RobotPy requires the Visual Studio 2022 redistributable:

1. Go to: https://visualstudio.microsoft.com/downloads/
2. Scroll down to "Tools for Visual Studio"
3. Download "Build Tools for Visual Studio 2022"
4. Run installer, select "Desktop development with C++"
5. Install (this takes a while)

#### Step 4: Verify Installation

Close all command prompts/PowerShell windows, open a new one, then:

```powershell
python --version
# Should show: Python 3.13.x

where python
# Should show: C:\Python313\python.exe

pip --version
# Should show pip and Python 3.13
```

---

## After Python is Set Up

Once Python is installed correctly, install the project dependencies:

```bash
# Mac
cd /path/to/rebuilt-1
pip3 install -r requirements.txt

# Windows
cd C:\path\to\rebuilt-1
pip install -r requirements.txt
```

## Troubleshooting

### "python not found" or wrong version shows up

- Make sure you closed and reopened your terminal after installation
- On Mac, use `python3` instead of `python`
- Check your PATH doesn't have old Python versions

### "pip not found"

Try:
```bash
# Mac
python3 -m pip --version

# Windows
python -m pip --version
```

### Multiple Python versions showing up

You didn't fully uninstall old versions. Go back to Step 1 and remove all old Python installations.

### Permission errors on Mac

Use `sudo` before commands, or check that Python was installed for all users.

### RobotPy won't install on Windows

Make sure you installed the Visual Studio Build Tools (Step 3 in Windows setup).

---

## Getting Help

- Ask Brian (coding mentor)
- Check the [RobotPy documentation](https://robotpy.readthedocs.io/)
- WPILib Python setup guide: https://docs.wpilib.org/en/stable/docs/zero-to-robot/step-2/python-setup.html
