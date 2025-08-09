import requests
import time
import threading
from queue import Queue
from colorama import Fore, init

init(autoreset=True)

ESP32_IP = "192.168.213.151"  # Change this to your ESP32 IP
BASE_URL = f"http://{ESP32_IP}"

led_queue = Queue()
led_thread = None
stop_led_thread = False

def _led_worker():
    """Background thread to process LED pattern commands from queue"""
    global stop_led_thread
    while not stop_led_thread:
        try:
            pattern = led_queue.get(timeout=0.1)
            if pattern == "STOP":
                break
            _send_led_command_direct(pattern)
            led_queue.task_done()
        except:
            continue

def _send_led_command_direct(pattern: str):
    """Send LED pattern command as simple GET request"""
    try:
        url = f"{BASE_URL}/style?name={pattern}"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"[LED] Sent pattern: {pattern}")
            return True
        else:
            print(Fore.RED + f"[LED ERROR] Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[LED ERROR] Cannot connect to ESP32: {e}")
        return False

def start_led_system():
    """Start the background LED command thread"""
    global led_thread, stop_led_thread
    if led_thread is None or not led_thread.is_alive():
        stop_led_thread = False
        led_thread = threading.Thread(target=_led_worker, daemon=True)
        led_thread.start()
        print("[LED] LED system started")

def stop_led_system():
    """Stop LED command thread cleanly"""
    global stop_led_thread
    stop_led_thread = True
    led_queue.put("STOP")
    if led_thread and led_thread.is_alive():
        led_thread.join(timeout=1)
    print("[LED] LED system stopped")

def send_led_pattern(pattern: str):
    """Send LED pattern asynchronously (non-blocking)"""
    start_led_system()
    try:
        led_queue.put_nowait(pattern)
        print(f"[LED] Queued pattern: {pattern}")
    except:
        print("[LED] Queue full, skipping pattern")

def send_led_pattern_blocking(pattern: str):
    """Send LED pattern synchronously (blocking)"""
    return _send_led_command_direct(pattern)

def test_connection():
    """Check if ESP32 is reachable"""
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=2)
        if response.status_code == 200:
            print(Fore.GREEN + "[LED] ESP32 connection OK")
            return True
        else:
            print(Fore.RED + "[LED] ESP32 responded with error")
            return False
    except:
        print(Fore.RED + "[LED] Cannot reach ESP32. Check IP and connection.")
        return False

# Convenient pattern functions
def start_startup_pattern():
    send_led_pattern("startup")

def start_listening_pattern():
    send_led_pattern("blue_loading")

def start_speaking_pattern():
    send_led_pattern("purple_speaking")

def start_processing_pattern():
    send_led_pattern("yellow_processing")

def led_good():
    send_led_pattern("green")

def led_too_loud():
    send_led_pattern("red")

def led_too_soft():
    send_led_pattern("orange")

def led_long_pause():
    send_led_pattern("red")

def led_off():
    send_led_pattern("off")
  
def stop_all_patterns():
    """Stop the LED command thread and turn off LEDs immediately."""
    global stop_led_thread
    # Turn off LEDs first
    _send_led_command_direct("off")
    # Stop the LED system so no more patterns run
    stop_led_thread = True
    led_queue.queue.clear()  # clear any pending patterns
    led_queue.put("STOP")    # signal thread to exit



if __name__ == "__main__":
    print("=== LED Controller Test ===")
    if test_connection():
        print("Testing LED patterns...")
        send_led_pattern_blocking("startup")
        time.sleep(3)
        start_listening_pattern()
        time.sleep(2)
        start_speaking_pattern()
        time.sleep(2)
        start_processing_pattern()
        time.sleep(2)
        led_good()
        time.sleep(1)
        led_too_loud()
        time.sleep(1)
        led_too_soft()
        time.sleep(1)
        led_off()
        print("LED test complete.")
    else:
        print("Check ESP32 IP and connection.")