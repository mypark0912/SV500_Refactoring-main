#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Must run as root
if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Please run as root (e.g., sudo $0 [--fresh|--init])"
  exit 1
fi

# Check argument count
if [[ $# -gt 1 ]]; then
    echo "Error: Too many arguments."
    echo "Usage: sudo $0 [--fresh|--init]"
    exit 1
fi

# Handle optional argument
FRESH_INSTALL=false
INIT_MODE=false
if [[ $# -eq 1 ]]; then
    case "$1" in
        --fresh|-fresh)
            FRESH_INSTALL=true
            ;;
        --init|-init)
            INIT_MODE=true
            ;;
        *)
            echo "Invalid option: $1"
            echo "Usage: sudo $0 [--fresh|--init]"
            exit 1
            ;;
    esac
fi

if [[ "$FRESH_INSTALL" == true ]]; then
    echo "==> Fresh install selected. Old project files will be removed."
elif [[ "$INIT_MODE" == true ]]; then
    echo "==> Init mode selected. Services will NOT be enabled/started (will be activated later by webserver initDB)."
else
    echo "==> Upgrade install. Existing project files will be preserved. Only smart systems service applications will be updated."
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
SERVICE_A="smartsystemsservice.service"
SERVICE_B="smartsystemsrestapiservice.service"

echo "==> Stopping and disabling services (if present)"
systemctl stop "$SERVICE_A" 2>/dev/null || true
systemctl stop "$SERVICE_B" 2>/dev/null || true
systemctl disable "$SERVICE_A" 2>/dev/null || true
systemctl disable "$SERVICE_B" 2>/dev/null || true

echo "==> Removing old systemd unit files (if present)"
rm -f "/etc/systemd/system/$SERVICE_A" || true
rm -f "/etc/systemd/system/$SERVICE_B" || true

echo "==> Reloading systemd units"
systemctl daemon-reload

echo "==> Removing previous application directories (if present)"
rm -rf /opt/service || true
rm -rf /opt/restapiservice || true

echo "==> Recreating directories and installing files"
install -d -m 755 /opt
# copy service trees; -a preserves modes/exec bits from your package
rsync -a --delete "$SCRIPT_DIR/service/" /opt/service/ 2>/dev/null || cp -r "$SCRIPT_DIR/service" /opt/
rsync -a --delete "$SCRIPT_DIR/restapiservice/" /opt/restapiservice/ 2>/dev/null || cp -r "$SCRIPT_DIR/restapiservice" /opt/

# ensure binaries are executable even if packaging missed it
chmod 755 /opt/service/smartsystemsservice 2>/dev/null || true
chmod 755 /opt/restapiservice/smartsystemsrestapiservice 2>/dev/null || true

echo "==> Installing systemd unit files"
install -m 644 "$SCRIPT_DIR/$SERVICE_A" "/etc/systemd/system/$SERVICE_A"
install -m 644 "$SCRIPT_DIR/$SERVICE_B" "/etc/systemd/system/$SERVICE_B"

if [[ "${1:-}" == "--fresh" || "${1:-}" == "-fresh" ]]; then
  echo "==> --fresh selected: resetting /usr/local/smartsystems and copying project files"
  rm -rf /usr/local/smartsystems || true
  install -d -m 755 /usr/local/smartsystems
  rsync -a "$SCRIPT_DIR/project/" /usr/local/smartsystems/project 2>/dev/null || cp -r "$SCRIPT_DIR/project/." /usr/local/smartsystems/project

else
  echo "==> Not fresh install: preserving and backing up factory.dat if exists"

  TARGET_DAT="/usr/local/smartsystems/project/factory.dat"
  NEW_DAT="$SCRIPT_DIR/project/factory.dat"

  if [[ -f "$TARGET_DAT" ]]; then
    TS=$(date +"%Y%m%d-%H%M%S")
    BACKUP="/usr/local/smartsystems/project/factory.${TS}.bak"
    echo "Backing up existing factory.dat to: $BACKUP"
    mv "$TARGET_DAT" "$BACKUP"
  fi

  echo "Copying new factory.dat to target"
  install -D -m 644 "$NEW_DAT" "$TARGET_DAT"
fi


echo "==> Reloading systemd units"
systemctl daemon-reload

if [[ "$INIT_MODE" == true ]]; then
    echo "==> --init mode: skipping enable/start (services will be enabled by webserver initDB)"
else
    echo "==> Enabling and starting services"
    systemctl enable "$SERVICE_A" --now
    systemctl enable "$SERVICE_B" --now

    echo "==> Status (short):"
    systemctl is-active "$SERVICE_A" || true
    systemctl is-active "$SERVICE_B" || true
fi

echo "Installation complete."
