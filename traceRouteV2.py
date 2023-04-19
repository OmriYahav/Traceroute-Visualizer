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

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def get_location_data(ip_address):
    """
    Retrieve location data (address, latitude, longitude) for a given IP address using the ip-api.com API.
    """
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f'HTTP error occurred while getting location data for {ip_address}: {e}')
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error occurred while getting location data for {ip_address}: {e}')
        return None

    try:
        data = response.json()
        latitude = data['lat']
        longitude = data['lon']
        geolocator = Nominatim(user_agent='traceroute-script')
        location = geolocator.reverse(f"{latitude}, {longitude}")
        return location.address, latitude, longitude
    except (KeyError, TypeError) as e:
        logger.error(f'Error occurred while parsing location data for {ip_address}: {e}')
        return None


@app.route('/')
def index():
    return render_template('index1.html')


@app.route('/traceroute', methods=['POST'])
def traceroute_route():
    dest_addr = request.form['destination_address']
    start_time = time_ns()
    logger.info(f'Starting traceroute to {dest_addr} at {start_time // (10 ** 9)} seconds')
    ans, unans = traceroute(dest_addr)
    coordinates = []
    unique_hops = set()
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'darkred', 'darkgreen', 'cadetblue', 'darkpurple', 'pink']
    color_index = 0
    map_location = folium.Map(location=[0, 0], zoom_start=2)

    for i, hop in enumerate(ans):
        ip_address = hop[1].src
        if ip_address not in unique_hops:
            unique_hops.add(ip_address)
            location_data = get_location_data(ip_address)
            if location_data:
                address, latitude, longitude = location_data
                logger.info(f'Hop {i + 1}: {ip_address}, {address}, Latitude: {latitude}, Longitude: {longitude}')
                coordinates.append([latitude, longitude])
                folium.Marker(location=[latitude, longitude],
                              tooltip=f'<b>Hop :{i + 1} IP :{ip_address}  Latitude : {latitude} Longitude: {longitude}</b>',
                              popup=f'<b>Hop {i + 1}: {ip_address}, {address}, Latitude: {latitude}, Longitude: {longitude}</b>',
                              icon=folium.Icon(color='green', icon_color='white', icon='ok-circle')).add_to(map_location)
                if i < len(ans) - 1:
                    next_hop = ans[i + 1][1].src
                    folium.PolyLine(locations=[(latitude, longitude), get_location_data(next_hop)[1:]],
                                    color=colors[color_index % len(colors)]).add_to(map_location)
                    color_index += 1
            else:
                logger.info(f'Hop {i + 1}: {ip_address} - could not retrieve location data')

    # map_location.save('hops.html')
    # webbrowser.open('hops.html')
    return render_template('index1.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5757)
