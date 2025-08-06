import requests
import time
import threading
from queue import Queue

ESP32_IP = "192.168.213.5"  # Make sure this IP is correct for your ESP32

# Threading control
gesture_queue = Queue()
gesture_thread = None
stop_gesture_thread = False

def _gesture_worker():
    """Background thread worker for sending gestures"""
    global stop_gesture_thread
    
    while not stop_gesture_thread:
        try:
            # Get gesture from queue with timeout
            gesture = gesture_queue.get(timeout=0.1)
            
            if gesture == "STOP":
                break
                
            # Send gesture immediately
            _send_gesture_direct(gesture)
            gesture_queue.task_done()
            
        except:
            # Queue empty or timeout - continue loop
            continue

def _send_gesture_direct(gesture: str):
    """Direct gesture sending without threading (internal use)"""
    try:
        url = f"http://{ESP32_IP}/preset?action={gesture}"
        response = requests.get(url, timeout=1)  # Reduced timeout for speed
        
        if response.status_code == 200:
            print(f"[GESTURE] Sent: {gesture}")
        else:
            print(f"[ERROR] Failed to send gesture. Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout when sending gesture: {gesture}")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to ESP32 at {ESP32_IP}")
    except Exception as e:
        print(f"[ERROR] Exception when sending gesture: {e}")

def start_gesture_system():
    """Initialize the real-time gesture system"""
    global gesture_thread, stop_gesture_thread
    
    if gesture_thread is None or not gesture_thread.is_alive():
        stop_gesture_thread = False
        gesture_thread = threading.Thread(target=_gesture_worker, daemon=True)
        gesture_thread.start()
        print("[GESTURE] Real-time gesture system started")

def stop_gesture_system():
    """Stop the gesture system"""
    global stop_gesture_thread
    
    stop_gesture_thread = True
    gesture_queue.put("STOP")  # Signal thread to stop
    
    if gesture_thread and gesture_thread.is_alive():
        gesture_thread.join(timeout=1)
    
    print("[GESTURE] Gesture system stopped")

def send_gesture(gesture: str):
    """Send gesture command to ESP32 in real-time (non-blocking)"""
    # Start system if not running
    start_gesture_system()
    
    # Add gesture to queue for immediate processing
    try:
        gesture_queue.put_nowait(gesture)
        print(f"[GESTURE] Queued: {gesture}")
    except:
        print(f"[GESTURE] Queue full, skipping: {gesture}")

def send_gesture_blocking(gesture: str):
    """Send gesture and wait for completion (blocking)"""
    _send_gesture_direct(gesture)

def send_gesture_sequence(gestures: list, delays: list = None):
    """Send a sequence of gestures with optional delays"""
    if delays is None:
        delays = [0.5] * len(gestures)  # Default 0.5s between gestures
    
    def sequence_worker():
        for i, gesture in enumerate(gestures):
            send_gesture(gesture)
            if i < len(delays):
                time.sleep(delays[i])
    
    # Run sequence in background
    sequence_thread = threading.Thread(target=sequence_worker, daemon=True)
    sequence_thread.start()

def test_connection():
    """Test if ESP32 is reachable"""
    try:
        response = requests.get(f"http://{ESP32_IP}/status", timeout=2)
        if response.status_code == 200:
            print("[GESTURE] ESP32 connection OK")
            return True
        else:
            print("[GESTURE] ESP32 responded but with error")
            return False
    except:
        print(f"[GESTURE] Cannot reach ESP32 at {ESP32_IP}")
        return False

def test_gestures():
    """Test all available gestures"""
    print("Testing ESP32 connection...")
    if not test_connection():
        return
        
    print("Starting real-time gesture test...")
    gestures = ["handsup", "handsdown", "handtogether", "handaway", "relax", "point"]
    
    # Test individual gestures with real-time sending
    for gesture in gestures:
        print(f"Testing gesture: {gesture}")
        send_gesture(gesture)
        time.sleep(1.5)  # Wait to see the gesture
    
    # Test rapid gestures (should not block)
    print("Testing rapid gesture sequence...")
    for gesture in ["handsup", "relax", "point", "relax", "handsdown"]:
        send_gesture(gesture)
        time.sleep(0.3)  # Very fast sequence
    
    print("Gesture test complete!")

def test_gesture_sequence():
    """Test gesture sequence functionality"""
    print("Testing gesture sequence...")
    
    # Welcome sequence
    welcome_gestures = ["relax", "handsup", "handtogether", "point", "relax"]
    welcome_delays = [0.5, 1.0, 1.0, 1.0, 0.5]
    
    send_gesture_sequence(welcome_gestures, welcome_delays)
    print("Gesture sequence started in background!")

# Auto-start the gesture system when imported
start_gesture_system()

if __name__ == "__main__":
    print("=== Real-time Gesture System Test ===")
    
    # Basic connection test
    test_connection()
    
    # Test individual gestures
    print("\n1. Testing individual gestures...")
    test_gestures()
    
    # Wait a bit
    time.sleep(2)
    
    # Test gesture sequences
    print("\n2. Testing gesture sequences...")
    test_gesture_sequence()
    
    # Wait for sequence to complete
    time.sleep(6)
    
    # Stop the system
    print("\n3. Stopping gesture system...")
    stop_gesture_system()