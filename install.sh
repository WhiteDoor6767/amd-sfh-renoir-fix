#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== AMD SFH Renoir 2-in-1 Tablet Fix Installer ==="
echo ""

# Check for root/sudo
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

# 1. Install DKMS module
echo "[1/4] Installing DKMS kernel module..."
$SUDO rm -rf /usr/src/amd_sfh-1.0
$SUDO cp -r "$SCRIPT_DIR/dkms" /usr/src/amd_sfh-1.0
$SUDO dkms remove -m amd_sfh -v 1.0 --all 2>/dev/null || true
$SUDO dkms add -m amd_sfh -v 1.0
$SUDO dkms build -m amd_sfh -v 1.0
$SUDO dkms install -m amd_sfh -v 1.0 --force

# 2. Reload module if already loaded
echo "[2/4] Loading patched amd_sfh driver..."
$SUDO modprobe -r amd_sfh 2>/dev/null || true
$SUDO modprobe amd_sfh

# 3. Setup user space rotation script and systemd daemon
USER_HOME=$(eval echo "~$SUDO_USER")
if [ -z "$SUDO_USER" ]; then
    USER_HOME="$HOME"
fi

echo "[3/4] Installing auto-rotation daemon for $USER_HOME..."
mkdir -p "$USER_HOME/.config/hypr/scripts"
mkdir -p "$USER_HOME/.config/systemd/user"

cp "$SCRIPT_DIR/scripts/auto_rotate.py" "$USER_HOME/.config/hypr/scripts/auto_rotate.py"
chmod +x "$USER_HOME/.config/hypr/scripts/auto_rotate.py"

cp "$SCRIPT_DIR/systemd/auto-rotate.service" "$USER_HOME/.config/systemd/user/auto-rotate.service"

# Chown if run via sudo
if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER:$SUDO_USER" "$USER_HOME/.config/hypr/scripts/auto_rotate.py"
    chown -R "$SUDO_USER:$SUDO_USER" "$USER_HOME/.config/systemd/user/auto-rotate.service"
fi

echo "[4/4] Enabling auto-rotate.service..."
if [ -n "$SUDO_USER" ]; then
    su - "$SUDO_USER" -c "systemctl --user daemon-reload && systemctl --user enable --now auto-rotate.service"
else
    systemctl --user daemon-reload && systemctl --user enable --now auto-rotate.service
fi

echo ""
echo "============================================================"
echo " Installation completed successfully!"
echo " DKMS status: $(dkms status amd_sfh)"
echo " Service status: Active (running)"
echo " Test by rotating your convertible physically!"
echo "============================================================"
