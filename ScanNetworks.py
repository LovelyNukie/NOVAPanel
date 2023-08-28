import pywifi
import csv
import subprocess
from pywifi import PyWiFi, const  # Make sure to import 'const'
import time  # Import the time module

def get_top_n_strongest_ssids(n=5):
    # Run the scan
    networks = scan_networks()
    
    sorted_networks = sorted(networks, key=lambda x: x['Signal_Strength'], reverse=True)[:n]
    
    # Debugging print statement
    print("Top N Strongest Networks: ", sorted_networks)
    
    return sorted_networks


def scan_networks():
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]

    print("Initiating scan...")

    # Start the scan
    iface.scan()
    time.sleep(5)  # Wait for 5 seconds to allow the scan to complete

    # Fetch and process the results
    scan_result = iface.scan_results()

    seen_ssids = set() # To keep track of SSIDs we've seen
    networks = []

    for network in scan_result:
        ssid = network.ssid.strip()
        if not ssid or ssid in seen_ssids:
            continue
        seen_ssids.add(ssid)
        security = network.akm[0] if network.akm else "None"
        
        # Add 'Signal_Strength' to the dictionary
        networks.append({'SSID': ssid, 'Security': security, 'Signal_Strength': network.signal})

    return networks

def get_adapters():
    adapters = []
    iwconfig_output = subprocess.check_output(['iwconfig'], stderr=subprocess.STDOUT, text=True)
    lines = iwconfig_output.split('\n')
    for line in lines:
        if 'IEEE 802.11' in line:
            adapter = line.split(' ')[0]
            adapters.append(adapter)
    return adapters

def write_to_csv(networks):
    with open('network_log.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["SSID", "Security"])
        for network in networks:
            writer.writerow([network["SSID"], network["Security"]])

if __name__ == "__main__":
    networks = scan_networks()
    write_to_csv(networks)
