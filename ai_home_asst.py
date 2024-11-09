import bluetooth
from machine import Pin
import network
import urequests
import json
import time
import struct
import gc
from _thread import start_new_thread

# Enable garbage collection
gc.enable()
gc.collect()

# WiFi credentials
SSID = "your_wifi_ssid"
PASSWORD = "your_wifi_passsword"

# Groq API settings
GROQ_API_KEY = "your_api_key"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# LED setup
led = Pin("LED", Pin.OUT)

# BLE constants
from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# BLE UART Service
UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)
UART_RX = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE)
UART_SERVICE = (UART_UUID, (UART_TX, UART_RX))

# LED control codes
LED_CONTROL_CODES = {
    "ON": "LED_CONTROL_ON",
    "OFF": "LED_CONTROL_OFF",
    "BLINK": "LED_CONTROL_BLINK"
}

def control_led(state="ON", delay=0.5, times=None, duration=None):
    """
    Controls the LED based on state and optional parameters.
    """
    def blink():
        end_time = time.time() + duration if duration else None
        for _ in range(times):
            if end_time and time.time() > end_time:
                break
            led.toggle()
            time.sleep(delay)
            led.toggle()
            time.sleep(delay)

    if state == "BLINK" and times is not None:
        if duration is None:
            duration = times * delay * 2
        start_new_thread(blink, ())
        return f"LED blinking started with delay={delay}s, times={times}, duration={duration}s"
    
    elif state == "ON":
        led.value(1)
        if duration:
            time.sleep(duration)
            led.value(0)
        return f"LED turned ON for {duration}s" if duration else "LED turned ON"
    
    elif state == "OFF":
        led.value(0)
        return "LED turned OFF"

def extract_control_code(response):
    for code in LED_CONTROL_CODES.values():
        if code in response:
            return code
    return None

def process_ai_response(response):
    control_code = extract_control_code(response)
    
    params = {}
    try:
        parts = response.split()
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=')
                params[key.lower()] = float(value)

        if control_code == "LED_CONTROL_ON":
            return True, control_led(state="ON", duration=params.get('duration'))
        
        elif control_code == "LED_CONTROL_OFF":
            return True, control_led(state="OFF")
        
        elif control_code == "LED_CONTROL_BLINK":
            delay = params.get('delay', 0.5)
            times = int(params.get('times', 10))
            duration = params.get('duration')
            return True, control_led(state="BLINK", delay=delay, times=times, duration=duration)

    except Exception as e:
        return False, f"Invalid parameters or error: {str(e)}"

    clean_response = response
    for code in LED_CONTROL_CODES.values():
        clean_response = clean_response.replace(code, "")
    return False, clean_response.strip()

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

def get_ai_response(user_input):
    gc.collect()
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GROQ_API_KEY}'
        }
        
        system_prompt = """Your name is Sol. You are a home automation assistant capable of controlling home devices and answering questions.
When responding to LED control commands:
- For turning ON the LED, include 'LED_CONTROL_ON duration=<seconds>' in your response
- For turning OFF the LED, include 'LED_CONTROL_OFF' in your response
- For blinking the LED, include 'LED_CONTROL_BLINK delay=<seconds> times=<number> duration=<seconds>' in your response
- Calculate parameters if needed:
  - delay = duration / (times * 2)
  - times = duration / (delay * 2)
  - duration = delay * times * 2
Place these control codes at the start of your response."""
        
        data = {
            "model": "llama3-groq-70b-8192-tool-use-preview",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.5,
            "max_tokens": 500,
            "top_p": 0.9,
            "stream": False,
            "stop": ["\n\n", "Human:", "Assistant:"]
        }

        print("Sending request to Groq...")
        response = None
        try:
            response = urequests.post(GROQ_ENDPOINT, json=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"API Error: {response.status_code}")
                return "I'm having trouble understanding right now. Please try again."
        except Exception as e:
            print(f"Request Error: {str(e)}")
            return "I'm having trouble connecting right now. Please try again."
        finally:
            if response:
                response.close()
            gc.collect()
            
    except Exception as e:
        print(f"General Error: {str(e)}")
        return "Error processing request"

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
        print("AI Assistant ready!")

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("Connected")
            self._notify("AI Assistant: Connected! Ask me anything.")
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            print("Disconnected")
            self._advertise()
            
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self._rx_handle:
                value = self._ble.gatts_read(self._rx_handle)
                try:
                    command = value.decode().strip()
                    print("Received:", command)
                    
                    if command.lower() == "exit":
                        self._notify("Goodbye!")
                        return
                        
                    self._notify("Processing request...")
                    ai_response = get_ai_response(command)
                    
                    if ai_response:
                        led_triggered, final_response = process_ai_response(ai_response)
                        self._notify(final_response)
                    else:
                        self._notify("No response from AI service")
                        
                except Exception as e:
                    print("Command Error:", str(e))
                    self._notify("Error processing command")

    def _notify(self, data):
        if not data:
            return
        for conn_handle in self._connections:
            try:
                chunks = [data[i:i+100] for i in range(0, len(data), 100)]
                for chunk in chunks:
                    self._ble.gatts_notify(conn_handle, self._tx_handle, chunk.encode())
                    time.sleep_ms(100)
            except Exception as e:
                print("Notification Error:", str(e))

    def _advertise(self, interval_us=100000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

def main():
    while True:
        try:
            wlan = connect_wifi()
            ble = BLESerial()
            while True:
                gc.collect()
                time.sleep_ms(100)
        except Exception as e:
            print("Main loop error:", str(e))
            time.sleep(5)

if __name__ == "__main__":
    main()

