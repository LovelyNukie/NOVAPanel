import gpsd

# Connect to the local gpsd
gpsd.connect()

# Get the latest reading
packet = gpsd.get_current()

# Print the latitude and longitude
print("Latitude:", packet.lat)
print("Longitude:", packet.lon)
