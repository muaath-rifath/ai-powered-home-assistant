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

def connect_wifi():
    """
    WiFi connection function
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(SSID, PASSWORD)
        
        max_wait = 10
        while max_wait > 0:
            if wlan.status() >= 3:
                break
            max_wait -= 1
            print('Waiting...')
            time.sleep(1)

        if wlan.status() != 3:
            raise RuntimeError('Network connection failed')
    
    print('Connected')
    status = wlan.ifconfig()
    print('IP:', status[0])
    return wlan

def main():
    try:
        wlan = connect_wifi()
        led.value(1)  # Indicate successful connection
        time.sleep(2)
        led.value(0)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    main()
