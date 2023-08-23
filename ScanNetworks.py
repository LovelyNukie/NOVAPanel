import pywifi
import csv
import subprocess

def scan_networks():
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    iface.scan()
    scan_result = iface.scan_results()

    seen_ssids = set() # To keep track of SSIDs we've seen
    networks = []

    for network in scan_result:
        ssid = network.ssid.strip() # Remove any leading/trailing whitespace

        # Ignore blank or duplicated SSIDs
        if not ssid or ssid in seen_ssids:
            continue

        # Add SSID to the set of seen SSIDs
        seen_ssids.add(ssid)

        security = network.akm[0] if network.akm else "None"
        networks.append({'SSID': ssid, 'Security': security})

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
