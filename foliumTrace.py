import logging
import os
import requests
import socket
from scapy.layers.inet import IP, ICMP, traceroute
from geopy.geocoders import Nominatim
from time import time_ns
import webbrowser
import folium
from flask import Flask, render_template, request, render_template_string

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

@app.route("/")
def fullscreen():
    """Simple example of a fullscreen map."""
    m = folium.Map()
    return m.get_root().render()

@app.route("/iframe")
def iframe():
    """Embed a map as an iframe on a page."""
    m = folium.Map()

    # set the iframe width and height
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()

    return render_template_string(
        """
            <!DOCTYPE html>
            <html>
                <head></head>
                <body>
                    <h1>Using an iframe</h1>
                    {{ iframe|safe }}
                </body>
            </html>
        """,
        iframe=iframe,
    )

@app.route("/components")
def components():
    """Extract map components and put those on a page."""
    m = folium.Map(
        width=800,
        height=600,
    )

    m.get_root().render()
    header = m.get_root().header.render()
    body_html = m.get_root().html.render()
    script = m.get_root().script.render()

    return render_template_string(
        """
            <!DOCTYPE html>
            <html>
                <head>
                    {{ header|safe }}
                </head>
                <body>
                    <h1>Using components</h1>
                    {{ body_html|safe }}
                    <script>
                        {{ script|safe }}
                    </script>
                </body>
            </html>
        """,
        header=header,
        body_html=body_html,
        script=script,
    )

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
    map_location = folium.Map(location=[0, 0], zoom_start=4)

    for i, hop in enumerate(ans):
        ip_address = hop[1].src
        if ip_address not in unique_hops:
            unique_hops.add(ip_address)
            location_data = get_location_data(ip_address)
            if location_data:
                address, latitude, longitude = location_data
                logger.info(f'Hop {i+1}: {ip_address}, {address}, Latitude: {latitude}, Longitude: {longitude}')
                coordinates.append([latitude, longitude])
                folium.Marker(location=[latitude, longitude], tooltip=f'<b>Hop :{i+1} IP :{ip_address}  lat : {latitude} lon: {longitude}</b>', popup=f'<b>{ip_address}</b>',icon=folium.Icon(color='green',icon_color='white',icon='ok-circle')).add_to(map_location)
                if i < len(ans) - 1:
                    next_hop = ans[i + 1][1].src
                    folium.PolyLine(locations=[(latitude, longitude), get_location_data(next_hop)[1:]], color=colors[color_index % len(colors)]).add_to(map_location)
                    color_index += 1
            else:
                logger.info(f'Hop {i+1}: {ip_address} - could not retrieve location data')


    map_location.save('hops.html')
    webbrowser.open('hops.html')
    return render_template('index1.html')

if __name__ == '__main__':
 app.run(host="0.0.0.0",port=5757)