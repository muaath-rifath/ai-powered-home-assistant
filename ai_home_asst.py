import bluetooth
from machine import Pin
import network
import time
import gc

# Enable garbage collection
gc.enable()
gc.collect()

# WiFi credentials
SSID = "ECE Dept Wi-Fi 1"
PASSWORD = "Wifi-1@Ece"

# LED setup
led = Pin("LED", Pin.OUT)

def main():
    print("Initial setup complete")

if __name__ == "__main__":
    main()
