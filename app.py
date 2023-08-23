from flask import Flask, jsonify, render_template, request
import ScanNetworks # Import your ScanNetworks.py functionality here
from ScanNetworks import get_adapters
import requests
import subprocess
import psutil
import os
import pandas as pd
if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")


app = Flask(__name__)
@app.route('/stats')
def get_stats():
    # Read data from CSV
    network_data = pd.read_csv('network_log.csv')

    # Analyze data to get all-time stats
    all_time_stats = analyze_data(network_data)

    # Analyze data to get in-range stats (modify as needed)
    in_range_stats = analyze_data(network_data)  # Modify as needed

    # Return the stats as JSON
    return jsonify(allTime=all_time_stats, inRange=in_range_stats)

def analyze_data(data):
    # Analyze the data and return the stats
    # Modify this function as needed
    return [10, 20, 30, 40, 50, 60]

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/get_cpu_usage', methods=['GET'])
def get_cpu_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    return jsonify({'cpu_usage': cpu_usage})
@app.route('/start_scanning', methods=['POST'])
def start_scanning():
    networks = ScanNetworks.scan_networks()
    print(networks)  # Print the networks to verify the data
    return jsonify(networks=networks)

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
