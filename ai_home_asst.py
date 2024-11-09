import bluetooth
from machine import Pin
import network
import time
import gc
import struct
from micropython import const

# Enable garbage collection
gc.enable()
gc.collect()

# WiFi credentials
SSID = "ECE Dept Wi-Fi 1"
PASSWORD = "Wifi-1@Ece"

# LED setup
led = Pin("LED", Pin.OUT)

# BLE constants
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# BLE UART Service
UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)
UART_RX = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE)
UART_SERVICE = (UART_UUID, (UART_TX, UART_RX))

def connect_wifi():
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
    ble = bluetooth.BLE()
    ble.active(True)
    print("BLE initialized")

if __name__ == "__main__":
    main()
