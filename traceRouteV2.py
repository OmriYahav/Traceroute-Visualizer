import logging
import os
import requests
import socket
from scapy.layers.inet import IP, ICMP, traceroute
from geopy.geocoders import Nominatim
from time import time_ns
import webbrowser
import folium
from flask import Flask, render_template, request

# create a Flask application instance
app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# create a logger object to be used for logging
logger = logging.getLogger()


def get_location_data(ip_address):
    """
    Retrieve location data (address, latitude, longitude) for a given IP address using the ip-api.com API.
    """
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}') # make a GET request to the ip-api.com API
        response.raise_for_status() # raise an exception if the response status code indicates an error
    except requests.exceptions.HTTPError as e:  # handle HTTP errors
        logger.error(f'HTTP error occurred while getting location data for {ip_address}: {e}')
        return None
    except requests.exceptions.RequestException as e: # handle other request errors
        logger.error(f'Request error occurred while getting location data for {ip_address}: {e}')
        return None

    try:
        data = response.json() # parse the response JSON
        latitude = data['lat'] # extract the latitude from the JSON
        longitude = data['lon'] # extract the longitude from the JSON
        geolocator = Nominatim(user_agent='traceroute-script') # create a geolocator instance
        location = geolocator.reverse(f"{latitude}, {longitude}") # reverse geocode the coordinates
        return location.address, latitude, longitude # return the address, latitude, and longitude as a tuple
    except (KeyError, TypeError) as e:  # handle errors in parsing the JSON or reverse geocoding
        logger.error(f'Error occurred while parsing location data for {ip_address}: {e}')
        return None


@app.route('/')
def index():
    return render_template('index1.html') # render an HTML template for the index page


@app.route('/traceroute', methods=['POST'])
def traceroute_route():
    dest_addr = request.form['destination_address'] # get the destination address from the form data
    start_time = time_ns()  # get the current time in nanoseconds
    logger.info(f'Starting traceroute to {dest_addr} at {start_time // (10 ** 9)} seconds') # log the start of the traceroute
    ans, unans = traceroute(dest_addr) # perform the traceroute and get the answered and unanswered packets
    coordinates = [] # initialize a list to store the coordinates of each hop
    unique_hops = set() # initialize a set to store the unique IP addresses of the hops
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'darkred', 'darkgreen', 'cadetblue', 'darkpurple', 'pink']
    color_index = 0  # initializes a color index to keep track of which color to use next
    map_location = folium.Map(location=[0, 0], zoom_start=2) # creates a new map with a starting location of [0,0] and zoom level of 2

    for i, hop in enumerate(ans): # iterates through each answered packet in the traceroute
        ip_address = hop[1].src # gets the source IP address of the current hop
        if ip_address not in unique_hops:  # checks if the IP address is unique
            unique_hops.add(ip_address) # adds the IP address to the set of unique hops
            location_data = get_location_data(ip_address)  # retrieves the latitude and longitude of the current hop from an external API
            if location_data:  # checks if the location data was successfully retrieved
                address, latitude, longitude = location_data # unpacks the location data into variables
                logger.info(f'Hop {i + 1}: {ip_address}, {address}, Latitude: {latitude}, Longitude: {longitude}') # logs the location data for the current hop
                coordinates.append([latitude, longitude]) # adds the coordinates to the list of coordinates
                folium.Marker(location=[latitude, longitude],  # adds a marker to the map for the current hop
                              tooltip=f'<b>Hop :{i + 1} IP :{ip_address}  Latitude : {latitude} Longitude: {longitude}</b>', # adds a tooltip with information about the hop
                              popup=f'<b>Hop {i + 1}: {ip_address}, {address}, Latitude: {latitude}, Longitude: {longitude}</b>', # adds a popup with detailed information about the hop
                              icon=folium.Icon(color='green', icon_color='white', icon='ok-circle')).add_to(map_location) # sets the marker's color and icon
                if i < len(ans) - 1:  # checks if this is not the last hop in the traceroute
                    next_hop = ans[i + 1][1].src  # gets the source IP address of the next hop
                    next_hop_location = get_location_data(next_hop)  # retrieve location data once
                    if next_hop_location:
                        _, next_latitude, next_longitude = next_hop_location
                        folium.PolyLine(
                            locations=[(latitude, longitude), (next_latitude, next_longitude)],
                            color=colors[color_index % len(colors)]
                        ).add_to(map_location)
                        color_index += 1
                    else:
                        logger.warning(f'Could not retrieve location data for next hop {next_hop}')
                # If location data is not available, log it and continue to the next hop

            else:
                logger.info(f'Hop {i + 1}: {ip_address} - could not retrieve location data')

    # Save the map as an HTML file and open it in a new browser tab
    map_location.save('hops.html')
    webbrowser.open('hops.html')
    # Render the index1.html template
    return render_template('index1.html')


if __name__ == '__main__':
    # Run the application on host 0.0.0.0 and port 5000
    app.run(host="0.0.0.0", port=5000)
