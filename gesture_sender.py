# gesture_sender.py
import socket

ESP32_IP = "192.168.1.xxx"  # Replace with your ESP32's IP
ESP32_PORT = 80

def send_gesture(gesture: str):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ESP32_IP, ESP32_PORT))
            sock.sendall((gesture + "\n").encode())
            print(f"[GESTURE] Sent: {gesture}")
    except Exception as e:
        print(f"[ERROR] Gesture send failed: {e}")
