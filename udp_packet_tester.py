#!/usr/bin/env python3

import socket
import time
from datetime import datetime

# Set the server's IP address and port
esp_ip = '192.168.1.105'  # Replace with your ESP32's IP address
esp_port = 3333  # The port should match the one in your ESP32 server code

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send 100 packets
for i in range(100):
    message = f"Packet {i+1}"
    try:
        # Get current time with milliseconds
        now = datetime.now()
        send_time = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format time string, truncate microseconds to milliseconds

        print(f"Sending {message} at {send_time}")

        # Send the packet
        sock.sendto(message.encode(), (esp_ip, esp_port))

        # Wait a short time before sending the next packet
        time.sleep(0.1)  # Adjust as necessary
    except Exception as e:
        print(f"Error: {e}")

# Close the socket
sock.close()

