import requests
import time

ESP32_IP = "192.168.213.5"  # Make sure this IP is correct for your ESP32

def send_gesture(gesture: str):
    """Send gesture command to ESP32"""
    try:
        url = f"http://{ESP32_IP}/preset?action={gesture}"
        response = requests.get(url, timeout=3)  # Increased timeout
        if response.status_code == 200:
            print(f"[GESTURE] Sent: {gesture}")
            # Removed the sleep delay for real-time gestures
        else:
            print(f"[ERROR] Failed to send gesture. Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout when sending gesture: {gesture}")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to ESP32 at {ESP32_IP}")
    except Exception as e:
        print(f"[ERROR] Exception when sending gesture: {e}")

def test_gestures():
    """Test all available gestures"""
    gestures = ["handsup", "handsdown", "handtogether", "handaway", "relax", "point"]
    
    for gesture in gestures:
        print(f"Testing gesture: {gesture}")
        send_gesture(gesture)
        time.sleep(2)  # Wait between gestures

if __name__ == "__main__":
    # Test the connection
    print("Testing ESP32 connection...")
    send_gesture("relax")
    
    # Uncomment below to test all gestures
    # test_gestures()