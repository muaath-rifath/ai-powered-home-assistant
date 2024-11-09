import bluetooth
from machine import Pin
import network
import time
import gc
from _thread import start_new_thread

# Enable garbage collection
gc.enable()
gc.collect()

# WiFi credentials
SSID = "ECE Dept Wi-Fi 1"
PASSWORD = "Wifi-1@Ece"

# LED setup
led = Pin("LED", Pin.OUT)

def control_led(state="ON", delay=0.5, times=None, duration=None):
    """
    Basic LED control function
    """
    def blink():
        for _ in range(times or 1):
            led.toggle()
            time.sleep(delay)
            led.toggle()
            time.sleep(delay)

    if state == "BLINK" and times is not None:
        start_new_thread(blink, ())
        return "LED blinking started"
    
    elif state == "ON":
        led.value(1)
        if duration:
            time.sleep(duration)
            led.value(0)
        return "LED turned ON"
    
    elif state == "OFF":
        led.value(0)
        return "LED turned OFF"

def main():
    control_led("BLINK", times=3)

if __name__ == "__main__":
    main()
