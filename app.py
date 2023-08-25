from flask import Flask, jsonify, render_template, request
import ScanNetworks # Import your ScanNetworks.py functionality here
from ScanNetworks import get_adapters
import requests
import subprocess
import psutil
import os
import pandas as pd
import gpsd
import gps
import time
import netifaces
from datetime import datetime
from pywifi import PyWiFi, const
import csv
from math import sin, cos, sqrt, atan2, radians
gpsd.connect()
if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
# Define the mapping function
def map_security_level(security):
    switcher = {
        0: 'None',
        1: 'WEP',
        2: 'WPA',
        3: 'WPA2',
        4: 'WPA3',
        # Add more cases if needed
    }
    return switcher.get(security, 'Unknown')

def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Converting coordinates from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Differences in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance * 1000  # Return distance in meters (convert from kilometers)
app = Flask(__name__)

@app.route('/initiate_scan', methods=['GET'])
def initiate_scan():
    # Get GPS data (existing function)
    gps_data = get_gps_data().get_json()

    # TODO: Call the function to perform network scan (to be implemented)
    networks = perform_network_scan()

    # Create a timestamp for the scan
    timestamp = datetime.now().isoformat()

    # Write the data to CSV
    with open('network_scans.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        for network in networks:
            writer.writerow([timestamp, gps_data['latitude'], gps_data['longitude'], network['ssid'], network['signal_strength']])

    return jsonify({'message': 'Scan initiated and data saved!', 'scan_data': networks})

def perform_network_scan():
    wifi = PyWiFi()
    iface = wifi.interfaces()[0] # Use the first available interface

    # Scan for networks
    iface.scan()
    scan_results = iface.scan_results()

    # Extract SSID and signal strength
    networks = []
    for result in scan_results:
        networks.append({
            'ssid': result.ssid,
            'signal_strength': result.signal
        })

    return networks

@app.route('/get_adapters', methods=['GET'])
def get_adapters():
    # Getting all the network interfaces
    interfaces = netifaces.interfaces()

    # Filtering only the wireless ones (usually start with 'wl')
    wireless_adapters = [interface for interface in interfaces if interface.startswith('wl')]

    return jsonify({'adapters': wireless_adapters})
def test_gps_adapter():
    try:
        response = requests.get('http://localhost:5000/get_gps_data')
        data = response.json()
        print("GPS Data:", data) # Debug print
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Check if latitude and longitude are populated (not zero)
        if latitude != 0 and longitude != 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error testing GPS adapter: {e}")
        return False

@app.route('/get_usb_devices', methods=['GET'])
def get_usb_devices():
    result = subprocess.run(['lsusb'], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')

    # Split the lines and extract only the name part
    usb_devices = [{"id": line.split(' ')[1], "name": " ".join(line.split(' ')[-4:]).strip()} for line in output.split('\n') if line]

    return jsonify({'usb_devices': usb_devices})


@app.route('/activate_gps_device', methods=['POST'])
def activate_gps_device():
    device_id = request.json['device_id']
    device_name = request.json['device_name']
    
    # Logic to activate and test the selected GPS device
    success = activate_and_test_device(device_id, device_name)

    if success:
        return jsonify({'message': 'GPS device activated successfully'})
    else:
        return jsonify({'message': 'Error fetching GPS device'}), 400

def activate_and_test_device(device_id, device_name):
    # Logic to bring up the adapter and test GPS
    # ...

    # Test the GPS adapter
    success = test_gps_adapter()
    
    return success if success else False

    return jsonify({'gps_devices': gps_devices})
@app.route('/get_gps_data', methods=['GET'])
def get_gps_data():
    packet = gpsd.get_current()
    return jsonify({
        'latitude': packet.lat,
        'longitude': packet.lon
    })
@app.route('/activate_gps_adapter', methods=['POST'])
def activate_gps_adapter():
    adapter = request.json['adapter']
    
    # Logic to activate the selected GPS adapter
    # ...

    return jsonify({'message': 'GPS adapter changed successfully'})
@app.route('/collect_data', methods=['POST'])
def collect_data():
    # Extracting the posted data
    data = request.json
    timestamp = data['timestamp']
    latitude = data['latitude']
    longitude = data['longitude']
    scanData = data['scanData']

    # Define the path to the CSV file
    csv_path = 'collected_scans.csv'

    # Append the data to the CSV file without clearing previous content
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        for scan in scanData:
            # Write the data for each scan
            writer.writerow([timestamp, latitude, longitude, scan['ssid'], scan['signal_strength']])

    return jsonify({'message': 'Data collected successfully!'})

def perform_network_triangulation():
    # Create an object for scanning networks
    wifi = PyWiFi()
    iface = wifi.interfaces()[0] # Use the first available interface
    
    # Scan for networks
    iface.scan()
    scan_results = iface.scan_results()
    
    # Get GPS data
    gps_data = get_gps_data().get_json()
    
    # Extract SSID, security level, signal strength, and GPS coordinates
    networks = []
    for result in scan_results:
        security = map_security_level(result.akm[0].value) if result.akm else 'Unknown'
        networks.append({
            'ssid': result.ssid,
            'security': security,
            'signal_strength': result.signal, # Signal quality
            'latitude': gps_data['latitude'],
            'longitude': gps_data['longitude']
        })

    return networks


def save_collected_data(networks):
    csv_path = 'collected_networks.csv'
    
    # Read existing contents of the CSV file (if any)
    try:
        existing_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['SSID', 'Security', 'Signal_Strength', 'Latitude', 'Longitude'])
    
    # Converting new scan results into a DataFrame
    new_df = pd.DataFrame(networks)
    
    # Concatenating old and new DataFrames (keeping duplicates since we want multiple observations)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Writing the concatenated DataFrame back to the CSV file
    combined_df.to_csv(csv_path, index=False)

@app.route('/start_scanning', methods=['POST'])
def start_scanning():
    # Get local-range networks by scanning and updating all-time data
    local_range_df = scan_and_update()
    print(local_range_df)  # Print the networks to verify the data
    return jsonify(networks=local_range_df.to_dict(orient='records'))
def read_collected_data(filename):
    data = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            timestamp, latitude, longitude, ssid, signal_strength = row
            data.append({
                'timestamp': timestamp,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'ssid': ssid,
                'signal_strength': int(signal_strength)
            })
    return data
def write_to_csv(networks):
    # Path to the CSV file
    csv_path = 'network_log.csv'

    # Reading existing contents of the CSV file (if any)
    try:
        existing_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['SSID', 'Security'])

    # Converting new scan results into a DataFrame
    new_df = pd.DataFrame(networks)

    # Concatenating old and new DataFrames, removing duplicates
    combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates()

    # Writing the concatenated DataFrame back to the CSV file
    combined_df.to_csv(csv_path, index=False)
def scan_and_update():
    # Scanning the networks
    local_range_networks = ScanNetworks.scan_networks()

    # Creating a DataFrame for local range networks
    local_range_df = pd.DataFrame(local_range_networks)

    # Path to the CSV files
    local_csv_path = 'network_log.csv'
    all_time_csv_path = 'collected_networks.csv'

    # Writing local range data to CSV
    local_range_df.to_csv(local_csv_path, index=False)

    # Reading existing contents of the all-time CSV file (if any)
    try:
        all_time_df = pd.read_csv(all_time_csv_path)
    except FileNotFoundError:
        all_time_df = pd.DataFrame(columns=['SSID', 'Security'])
    
    # Concatenating old and new DataFrames
    combined_df = pd.concat([all_time_df, local_range_df], ignore_index=True)

    # Removing duplicates based on SSID
    combined_df.drop_duplicates(subset=['SSID'], inplace=True)

    # Writing the combined DataFrame back to the all-time CSV file
    combined_df.to_csv(all_time_csv_path, index=False)

    return local_range_df


def analyze_all_time_data():
    csv_path = 'collected_networks.csv'
    
    # Dictionary to store the count of each security type, including 'None'
    security_counts = {str(i): 0 for i in range(4)}
    security_counts['None'] = 0  # Add the 'None' key

    try:
        with open(csv_path, 'r') as file:
            next(file)  # Skip the header line
            for line in file:
                # Split the line by comma
                parts = line.strip().split(',')
                
                # Get the security value, assuming it's the second part of the line
                security_value = parts[1]
                
                # Increment the count for this security value
                if security_value in security_counts:
                    security_counts[security_value] += 1
                else:
                    security_counts['None'] += 1  # Increment the count for 'None' if the value is not recognized

        # Convert the counts to a list in the desired order
        stats = [security_counts[str(i)] for i in range(4)]
        stats.append(security_counts['None'])  # Add the count for 'None'
        
        return stats

    except FileNotFoundError:
        print("File not found!")
        return [0, 0, 0, 0, 0]
def analyze_local_range_data():
    csv_path = 'network_log.csv'
    
    # Dictionary to store the count of each security type, including 'None'
    security_counts = {str(i): 0 for i in range(4)}
    security_counts['None'] = 0  # Add the 'None' key

    try:
        with open(csv_path, 'r') as file:
            next(file)  # Skip the header line
            for line in file:
                # Split the line by comma
                parts = line.strip().split(',')
                
                # Get the security value, assuming it's the second part of the line
                security_value = parts[1]
                
                # Increment the count for this security value
                if security_value in security_counts:
                    security_counts[security_value] += 1
                else:
                    security_counts['None'] += 1  # Increment the count for 'None' if the value is not recognized

        # Convert the counts to a list in the desired order
        stats = [security_counts[str(i)] for i in range(4)]
        stats.append(security_counts['None'])  # Add the count for 'None'
        
        return stats

    except FileNotFoundError:
        print("File not found!")
        return [0, 0, 0, 0, 0]
def save_all_time_data():
    # Path to the CSV files
    network_log_path = 'network_log.csv'
    collected_networks_path = 'collected_networks.csv'

    # Reading existing contents of both CSV files
    try:
        existing_network_log_df = pd.read_csv(network_log_path)
    except FileNotFoundError:
        existing_network_log_df = pd.DataFrame(columns=['SSID', 'Security'])

    try:
        collected_networks_df = pd.read_csv(collected_networks_path)
    except FileNotFoundError:
        collected_networks_df = pd.DataFrame(columns=['SSID', 'Security'])

    # Concatenating the DataFrames and removing duplicates
    all_time_df = pd.concat([existing_network_log_df, collected_networks_df], ignore_index=True).drop_duplicates()

    # Writing the concatenated DataFrame back to the collected_networks.csv file
    all_time_df.to_csv(collected_networks_path, index=False)

    # Clearing the network_log.csv file
    existing_network_log_df.iloc[0:0].to_csv(network_log_path, index=False)

# Call this function before starting the scanning process
save_all_time_data()

@app.route('/get_stats', methods=['GET'])
def get_stats():
    # Get local range stats and all-time stats
    local_range_stats = analyze_local_range_data()
    all_time_stats = analyze_all_time_data()

    # Combine or format the stats as needed
    stats = {
        'local_range_stats': local_range_stats,
        'all_time_stats': all_time_stats
    }

    return jsonify(stats)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/get_cpu_usage', methods=['GET'])
def get_cpu_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    return jsonify({'cpu_usage': cpu_usage})


@app.route('/get_adapters', methods=['GET'])
def fetch_adapters():
    adapters = get_adapters()
    return jsonify({'adapters': adapters})

@app.route('/activate_adapter', methods=['POST'])
def activate_adapter():
    adapter = request.json['adapter']
    
    # Bring up the adapter (if it's down)
    bring_up_cmd = f"sudo ip link set {adapter} up"
    subprocess.run(bring_up_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if the adapter is up
    status_cmd = f"ip link show {adapter}"
    result = subprocess.run(status_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    status_output = result.stdout.decode('utf-8')
    
    # Check if the adapter is in the 'UP' state
    success = "UP" in status_output

    return jsonify({'status': 'success' if success else 'failure'})
@app.route('/analytics')
def analytics():
    return render_template('analytics.html')
@app.route('/map')
def map():
    return render_template('map.html')
@app.route('/get_adapter_state', methods=['GET'])
def get_adapter_state():
    adapter = 'wlan0'  # Replace with your logic to get the selected adapter
    cmd = f'ip link show {adapter}'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    print(f"Adapter Output: {output}")  # Debug print

    if "UP" in output:
        state = 'active'
    else:
        state = 'idle'
    return jsonify({'state': state})
if __name__ == '__main__':   
    app.run(debug=True)
