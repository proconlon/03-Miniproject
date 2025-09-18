import network
import urequests
import time
from machine import Pin

# Replace with your WiFi credentials
# Currently Testing with Hotspot
ssid = "Hieu's iPhone"
password = "Welovebls"

#Change below depending on wifi as well
# IP address of your laptop running the Flask server
server_ip = "172.20.10.3"  # Replace with your laptop's IP
server_url = f"http://{server_ip}:5000/signal"


# Setup signal detection (e.g., using GPIO pin 15 as input)
# Set the pin to light detection pin
signal_pin = Pin(15, Pin.IN)

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

print("Connecting to WiFi...", end="")
while not wlan.isconnected():
    time.sleep(0.5)
    print(".", end="")
print("\nConnected to WiFi:", wlan.ifconfig())

# Main loop
while True:
    if signal_pin.value():  # signal detected (e.g., button pressed)
        try:
            response = urequests.post(server_url)
            print("Signal sent:", response.text)
            response.close()
        except Exception as e:
            print("Failed to send signal:", e)
    time.sleep(2)  # delay to avoid spamming
