FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000

# Scapy needs NET_RAW capability. Run with:
# docker run --cap-add=NET_RAW --cap-add=NET_ADMIN -p 5000:5000 traceroute-visualizer
CMD ["python", "-m", "traceroute_visualizer.app"]
