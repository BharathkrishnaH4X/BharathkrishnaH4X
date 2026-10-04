#!/bin/bash

clear

cat << 'EOF'
 _    _        _                        _
| |  | |      (_)                      | |
| |__| |  ___  _    ___   ___   ___    | |__    ___  ____  __ _
|  __  | / _ \| |  / __| / _ \ | __ \  |  _ \  / _ \| __/ / _  |
| |  | ||  __/| |  \__ \\  __/ | | | | | |_) ||  __/| |  ( |_| |
|_|  |_| \___||_| /____/ \___| |_| |_| |____/  \___||_|   \__, |
                                                           __/ |
                                                          |___/

                    - A Dedsec Code
EOF

echo
echo "************************************************************"
echo "* Copyright of BharathkrishnaH4X - Dedsec, 2026           *"
echo "* https://github.com/BharathkrishnaH4X                    *"
echo "************************************************************"
echo

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "************ Try running this program with sudo. *************"
    exit 1
fi

# Check required tools
for tool in iwconfig airmon-ng airodump-ng; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[!] $tool is not installed."
        exit 1
    fi
done

# Find wireless interfaces
echo "[+] Detecting WiFi interfaces..."
echo

interfaces=($(iwconfig 2>/dev/null | awk '/^[a-zA-Z0-9]+[[:space:]]+IEEE 802.11/ {print $1}'))

if [ ${#interfaces[@]} -eq 0 ]; then
    echo "[!] No WiFi interface found."
    echo "[!] Connect a compatible WiFi adapter and try again."
    exit 1
fi

echo "The following WiFi interfaces are available:"
echo

for i in "${!interfaces[@]}"; do
    echo "$i - ${interfaces[$i]}"
done

echo

# Select interface
while true; do
    read -p "Select the interface: " choice

    if [[ "$choice" =~ ^[0-9]+$ ]] &&
       [ "$choice" -ge 0 ] &&
       [ "$choice" -lt "${#interfaces[@]}" ]; then
        break
    fi

    echo "[!] Please enter a valid number."
done

WLAN="${interfaces[$choice]}"

echo
echo "[+] WiFi adapter selected: $WLAN"

# Kill conflicting processes
echo
echo "[+] Killing conflicting processes..."
airmon-ng check kill

# Enable monitor mode
echo
echo "[+] Enabling monitor mode..."
airmon-ng start "$WLAN"

MON="${WLAN}mon"

# Verify monitor interface
if ! iwconfig "$MON" >/dev/null 2>&1; then
    echo "[!] Monitor interface $MON was not created."
    exit 1
fi

echo
echo "[+] Monitor mode enabled on: $MON"
echo

# Start AP discovery
echo "[+] Starting wireless network discovery..."
echo "[+] Press Ctrl+C when finished scanning."
echo

airodump-ng "$MON"

# Cleanup
echo
echo "[+] Stopping monitor mode..."
airmon-ng stop "$MON"

echo
echo "[+] Done."
