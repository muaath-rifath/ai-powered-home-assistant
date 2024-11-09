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

class BLESerial:
    def __init__(self, name="Pico-AI"):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((UART_SERVICE,))
        
        self._connections = set()
        self._payload = bytearray()
        
        # Advertising payload setup
        self._payload.extend(struct.pack("BB", 2, 0x01))
        name_bytes = name.encode()
        self._payload.extend(struct.pack("BB", len(name_bytes) + 1, 0x09))
        self._payload.extend(name_bytes)
        self._payload.extend(b'\x03\x03')
        self._payload.extend(b'\x6E\x40')
        
        self._advertise()
        print("BLE Serial initialized")

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("Connected")
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            print("Disconnected")
            self._advertise()

    def _advertise(self, interval_us=100000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

def main():
    ble = BLESerial()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
