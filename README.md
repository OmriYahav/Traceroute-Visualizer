# 🌎 Traceroute Visualizer 🌐

This project is a web application that allows users to visualize the path that internet packets take from their computer to a specified destination. 

## 🚀 Getting Started
1. Clone this repository.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Run `python traceRouteV2.py` to start the web server.
4. Open your web browser and go to `http://localhost:5000` to use the application.

## 📸 Screenshots


![This is an image](img/TraceOnMapPage.PNG)


![This is an image](img/HopsOnMap.PNG)

## 🧰 Technologies Used
- Python
- Flask
- Scapy
- Geopy
- Folium

## 🤔 How It Works
The user inputs a destination IP address into a web form, and the application sends a series of packets to that address using the Scapy library's traceroute function. The application then extracts the IP addresses of each router that the packets pass through and uses the Geopy library to retrieve the latitude and longitude of each router. Finally, the application uses the Folium library to create a map that visualizes the path of the packets, with markers indicating the location of each router and lines connecting them.

## 🌟 Features
- Interactive map that allows users to zoom in and out and click on markers for more information
- Color-coded lines between routers to help users distinguish between different parts of the path
- Automatic reverse geocoding of router locations to display the name of the city and country where each router is located

## 🤝 Contributing
Contributions are welcome! If you find a bug or have a feature request, please create an issue. If you want to contribute code, please fork the repository and submit a pull request.

## 📝 License
This project is licensed under the MIT License. See the LICENSE file for details.
