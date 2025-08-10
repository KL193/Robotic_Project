import requests
import time

# ESP32 Configuration
ESP32_IP = "192.168.213.5"

# Gesture mapping for backward compatibility
GESTURE_MAPPING = {
    "relax": "relax",
    "point": "point", 
    "handaway": "handaway",
    "handtogether": "handtogether",
    "handsdown": "handsdown",
    "handsup": "handaway",  # Map handsup to handaway for ESP32
}

def send_gesture(gesture_name, timeout=1):
    """
    Enhanced gesture sender with better error handling and compatibility
    
    Args:
        gesture_name (str): Name of the gesture to send
        timeout (float): Request timeout in seconds
        
    Returns:
        bool: True if gesture sent successfully, False otherwise
    """
    # Map gesture name if needed
    esp32_gesture = GESTURE_MAPPING.get(gesture_name, "relax")
    
    url = f"http://{ESP32_IP}/preset?action={esp32_gesture}"
    
    try:
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            print(f"✅ Gesture '{esp32_gesture}' sent successfully to ESP32")
            return True
        else:
            print(f"⚠️ ESP32 responded with status {response.status_code} for gesture '{esp32_gesture}'")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout sending gesture '{esp32_gesture}' to ESP32")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error sending gesture '{esp32_gesture}' to ESP32")
        return False
    except Exception as e:
        print(f"❌ Error sending gesture '{esp32_gesture}': {e}")
        return False

def test_esp32_connection():
    """
    Test ESP32 connectivity
    
    Returns:
        bool: True if ESP32 is reachable, False otherwise
    """
    try:
        response = requests.get(f"http://{ESP32_IP}/preset?action=relax", timeout=2)
        if response.status_code == 200:
            print(f"✅ ESP32 at {ESP32_IP} is reachable")
            return True
        else:
            print(f"⚠️ ESP32 responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ESP32 connection test failed: {e}")
        return False

def send_gesture_sequence(gestures, delay=1.0):
    """
    Send a sequence of gestures with delays
    
    Args:
        gestures (list): List of gesture names
        delay (float): Delay between gestures in seconds
        
    Returns:
        bool: True if all gestures sent successfully
    """
    success_count = 0
    
    for i, gesture in enumerate(gestures):
        print(f"Sending gesture {i+1}/{len(gestures)}: {gesture}")
        if send_gesture(gesture):
            success_count += 1
        
        if i < len(gestures) - 1:  # Don't delay after last gesture
            time.sleep(delay)
    
    success_rate = success_count / len(gestures) if gestures else 0
    print(f"Gesture sequence completed: {success_count}/{len(gestures)} successful ({success_rate*100:.1f}%)")
    
    return success_rate == 1.0

if __name__ == "__main__":
    # Test the gesture sender
    print("🧪 Testing ESP32 gesture sender...")
    
    if test_esp32_connection():
        # Test basic gestures
        test_gestures = ["relax", "point", "handaway", "handtogether", "handsdown", "relax"]
        print(f"\n🎭 Testing gesture sequence: {test_gestures}")
        send_gesture_sequence(test_gestures, delay=2.0)
    else:
        print("❌ Cannot test gestures - ESP32 not reachable")
        print("Please check:")
        print("1. ESP32 is powered on")
        print("2. ESP32 is connected to WiFi") 
        print("3. IP address is correct:", ESP32_IP)
        print("4. ESP32 web server is running")