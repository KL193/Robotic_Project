import requests
import time
import threading
from colorama import Fore, init

init(autoreset=True)

# ESP32 Configuration
ESP32_IP = "10.32.11.70"  # Change this to your ESP32's IP address
ESP32_PORT = 80
BASE_URL = f"http://{ESP32_IP}:{ESP32_PORT}"

# Global pattern control
current_pattern_thread = None
stop_pattern = False

def send_led_command(pattern, brightness=100, speed=500):
    """
    Send LED pattern command to ESP32
    
    Args:
        pattern: 'startup', 'blue_loading', 'purple_speaking', 'yellow_processing', 'red', 'green', 'orange', 'off'
        brightness: 0-255 (default 100)
        speed: pattern speed in ms (default 500)
    """
    try:
        url = f"{BASE_URL}/led"
        data = {
            "pattern": pattern,
            "brightness": brightness,
            "speed": speed
        }
        
        response = requests.post(url, json=data, timeout=2)
        
        if response.status_code == 200:
            print(f"[LED] {pattern.upper()} - Brightness: {brightness}")
            return True
        else:
            print(Fore.RED + f"[LED ERROR] Status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[LED ERROR] Cannot connect to ESP32: {e}")
        return False

def stop_current_pattern():
    """Stop any running LED pattern"""
    global stop_pattern, current_pattern_thread
    stop_pattern = True
    if current_pattern_thread and current_pattern_thread.is_alive():
        current_pattern_thread.join(timeout=1)
    stop_pattern = False

def start_pattern_thread(pattern_func, *args):
    """Start a new pattern in a separate thread"""
    global current_pattern_thread
    stop_current_pattern()
    current_pattern_thread = threading.Thread(target=pattern_func, args=args)
    current_pattern_thread.daemon = True
    current_pattern_thread.start()

# ===== BEAUTIFUL LED PATTERNS =====

def startup_pattern():
    """Beautiful startup pattern for 40 seconds"""
    print(Fore.CYAN + "[LED] Starting beautiful startup pattern for 40 seconds...")
    send_led_command("startup", brightness=120, speed=300)
    
    # Let ESP32 handle the 40-second pattern
    start_time = time.time()
    while time.time() - start_time < 40 and not stop_pattern:
        time.sleep(0.5)
    
    if not stop_pattern:
        print(Fore.GREEN + "[LED] Startup pattern complete!")

def blue_loading_pattern():
    """Blue loading pattern for listening"""
    print(Fore.BLUE + "[LED] Blue loading pattern - Listening...")
    send_led_command("blue_loading", brightness=100, speed=400)

def purple_speaking_pattern():
    """Purple pattern when robot is speaking"""
    print(Fore.MAGENTA + "[LED] Purple speaking pattern...")
    send_led_command("purple_speaking", brightness=110, speed=600)

def yellow_processing_pattern():
    """Pale yellow pattern for analysis and optimization"""
    print(Fore.YELLOW + "[LED] Yellow processing pattern...")
    send_led_command("yellow_processing", brightness=80, speed=800)

# ===== SIMPLE LED STATES (for real-time feedback) =====

def led_good():
    """Light up GREEN - Everything is good"""
    stop_current_pattern()
    send_led_command("green", brightness=80)

def led_too_loud():
    """Light up RED - Too loud"""
    stop_current_pattern()
    send_led_command("red", brightness=120)

def led_too_soft():
    """Light up ORANGE - Too soft"""
    stop_current_pattern()
    send_led_command("orange", brightness=100)

def led_long_pause():
    """Light up RED - Long pause detected"""
    stop_current_pattern()
    send_led_command("red", brightness=150)

def led_off():
    """Turn off LEDs"""
    stop_current_pattern()
    send_led_command("off", brightness=0)

# ===== HIGH-LEVEL PATTERN FUNCTIONS =====

def start_startup_pattern():
    """Start the 40-second startup pattern"""
    start_pattern_thread(startup_pattern)

def start_listening_pattern():
    """Start blue loading pattern for listening"""
    start_pattern_thread(blue_loading_pattern)

def start_speaking_pattern():
    """Start purple pattern for robot speaking"""
    start_pattern_thread(purple_speaking_pattern)

def start_processing_pattern():
    """Start yellow pattern for analysis/optimization"""
    start_pattern_thread(yellow_processing_pattern)

def stop_all_patterns():
    """Stop all patterns and turn off LEDs"""
    stop_current_pattern()
    led_off()

def test_connection():
    """Test if ESP32 is reachable"""
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=3)
        if response.status_code == 200:
            print(Fore.GREEN + "[LED] ESP32 connection OK")
            return True
        else:
            print(Fore.RED + "[LED] ESP32 responded but with error")
            return False
    except:
        print(Fore.RED + "[LED] Cannot reach ESP32. Check IP address and connection.")
        return False

# Test the connection when imported
if __name__ == "__main__":
    print("Testing ESP32 connection...")
    if test_connection():
        print("Testing LED patterns...")
        
        # Test startup pattern (shortened for testing)
        print("Testing startup pattern...")
        send_led_command("startup", brightness=120, speed=300)
        time.sleep(3)
        
        # Test other patterns
        print("Testing blue loading...")
        start_listening_pattern()
        time.sleep(2)
        
        print("Testing purple speaking...")
        start_speaking_pattern()
        time.sleep(2)
        
        print("Testing yellow processing...")
        start_processing_pattern()
        time.sleep(2)
        
        # Test feedback colors
        print("Testing feedback colors...")
        led_good()
        time.sleep(1)
        led_too_loud()
        time.sleep(1)
        led_too_soft()
        time.sleep(1)
        
        # Turn off
        led_off()
        print("Test complete!")
    else:
        print("Please check ESP32 IP address and make sure it's running.")