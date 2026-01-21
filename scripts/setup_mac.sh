#!/bin/bash
#
# Team 9771 FPRO - Mac Python Setup Script
# Removes old Python versions and installs Python 3.13 globally
#
# Usage: sudo ./setup_mac.sh
#

set -e

PYTHON_VERSION="3.13.1"
PYTHON_MAJOR="3.13"
PKG_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.pkg"
PKG_FILE="/tmp/python-${PYTHON_VERSION}.pkg"

echo "========================================"
echo "Team 9771 FPRO - Python Setup for Mac"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Remove old Python versions"
echo "  2. Install Python ${PYTHON_VERSION} globally"
echo "  3. Set up PATH for all users"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run with sudo:"
    echo "  sudo ./setup_mac.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo "Running as: $ACTUAL_USER"
echo ""

# --- Step 1: Remove old Python versions ---
echo "Step 1: Removing old Python versions..."
echo ""

# Remove Homebrew Python versions
if command -v brew &> /dev/null; then
    echo "  Checking Homebrew Python..."
    # Run as the actual user, not root
    sudo -u "$ACTUAL_USER" brew uninstall --ignore-dependencies python python@3.8 python@3.9 python@3.10 python@3.11 python@3.12 python@3.14 2>/dev/null || true
fi

# Remove old python.org framework installations
echo "  Checking Python framework installations..."
for version in 3.8 3.9 3.10 3.11 3.12 3.14; do
    if [ -d "/Library/Frameworks/Python.framework/Versions/$version" ]; then
        echo "    Removing Python $version framework..."
        rm -rf "/Library/Frameworks/Python.framework/Versions/$version"
    fi
    if [ -d "/Applications/Python $version" ]; then
        echo "    Removing Python $version application folder..."
        rm -rf "/Applications/Python $version"
    fi
done

# Clean up old symlinks in /usr/local/bin
echo "  Cleaning up old symlinks..."
for f in /usr/local/bin/python* /usr/local/bin/pip* /usr/local/bin/idle* /usr/local/bin/pydoc* /usr/local/bin/2to3*; do
    if [ -L "$f" ]; then
        # Only remove if it's a symlink to an old Python version
        target=$(readlink "$f" 2>/dev/null || true)
        if [[ "$target" == *"Python.framework"* ]] && [[ "$target" != *"$PYTHON_MAJOR"* ]]; then
            echo "    Removing old symlink: $f"
            rm -f "$f"
        fi
    fi
done

echo "  Old Python versions removed."
echo ""

# --- Step 2: Download Python ---
echo "Step 2: Downloading Python ${PYTHON_VERSION}..."
echo "  URL: $PKG_URL"
echo ""

if [ -f "$PKG_FILE" ]; then
    rm "$PKG_FILE"
fi

curl -L -o "$PKG_FILE" "$PKG_URL"

if [ ! -f "$PKG_FILE" ]; then
    echo "ERROR: Failed to download Python installer"
    exit 1
fi

echo "  Download complete."
echo ""

# --- Step 3: Install Python ---
echo "Step 3: Installing Python ${PYTHON_VERSION} (this may take a minute)..."
echo ""

installer -pkg "$PKG_FILE" -target /

echo "  Installation complete."
echo ""

# Clean up
rm -f "$PKG_FILE"

# --- Step 4: Set up PATH for all users ---
echo "Step 4: Setting up PATH for all users..."
echo ""

PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/${PYTHON_MAJOR}/bin"

# Create /etc/paths.d entry for system-wide PATH
echo "  Adding Python to system PATH..."
echo "$PYTHON_BIN" > /etc/paths.d/python${PYTHON_MAJOR//./}

# Also set up the user's shell profile
echo "  Configuring shell profile for $ACTUAL_USER..."

# Determine shell config file
if [ -f "$ACTUAL_HOME/.zshrc" ] || [ "$SHELL" = "/bin/zsh" ]; then
    SHELL_CONFIG="$ACTUAL_HOME/.zprofile"
else
    SHELL_CONFIG="$ACTUAL_HOME/.bash_profile"
fi

# Remove old Python PATH entries and add new one
if [ -f "$SHELL_CONFIG" ]; then
    # Remove old entries
    sed -i '' '/Python.framework/d' "$SHELL_CONFIG" 2>/dev/null || true
    sed -i '' '/alias python=python3/d' "$SHELL_CONFIG" 2>/dev/null || true
    sed -i '' '/alias pip=pip3/d' "$SHELL_CONFIG" 2>/dev/null || true
fi

# Add new entries
cat >> "$SHELL_CONFIG" << 'PROFILE_EOF'

# Python 3.13 - Team 9771 FPRO setup
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
alias python=python3
alias pip=pip3
PROFILE_EOF

# Fix ownership
chown "$ACTUAL_USER" "$SHELL_CONFIG"

echo "  PATH configured."
echo ""

# --- Step 5: Create convenient symlinks ---
echo "Step 5: Creating symlinks..."
echo ""

# Create symlinks in /usr/local/bin for convenience
mkdir -p /usr/local/bin

ln -sf "${PYTHON_BIN}/python3" /usr/local/bin/python3
ln -sf "${PYTHON_BIN}/python3" /usr/local/bin/python
ln -sf "${PYTHON_BIN}/pip3" /usr/local/bin/pip3
ln -sf "${PYTHON_BIN}/pip3" /usr/local/bin/pip

echo "  Symlinks created."
echo ""

# --- Step 6: Verify installation ---
echo "Step 6: Verifying installation..."
echo ""

INSTALLED_VERSION=$("${PYTHON_BIN}/python3" --version 2>&1)
echo "  Installed: $INSTALLED_VERSION"

if [[ "$INSTALLED_VERSION" == *"$PYTHON_MAJOR"* ]]; then
    echo "  SUCCESS!"
else
    echo "  WARNING: Version mismatch. Expected Python $PYTHON_MAJOR"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "IMPORTANT: Close this terminal and open a new one."
echo ""
echo "Then verify with:"
echo "  python3 --version"
echo "  which python3"
echo ""
echo "Next steps:"
echo "  cd /path/to/rebuilt-1"
echo "  pip3 install -r requirements.txt"
echo ""
