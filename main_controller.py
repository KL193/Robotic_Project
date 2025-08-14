import os
import threading
import pygame
import subprocess
import sys
import time
from speakz_greeting import speak_text, recognize_speech, speak_greeting, update_practice_log, ask_practice
from gesture_sender import send_gesture
from led_controller import (
    start_startup_pattern, start_listening_pattern,
    start_speaking_pattern, start_processing_pattern,
    stop_all_patterns, test_connection
)

CHIME_AUDIO_FILE = "sound.mp3"
QUOTE = "The way to get started is to quit talking and begin doing."

# ------------------- STARTUP FUNCTIONS -------------------

def play_chime():
    """Play the chime audio and return when it finishes"""
    pygame.mixer.init()
    pygame.mixer.music.load(CHIME_AUDIO_FILE)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def synchronized_startup():
    """Run chime and LED startup pattern simultaneously, wait for both to complete"""
    print("🚀 Starting synchronized startup sequence...")
    
    led_thread = threading.Thread(target=start_startup_pattern)
    chime_thread = threading.Thread(target=play_chime)
    
    led_thread.start()
    chime_thread.start()
    
    led_thread.join()
    chime_thread.join()
    
    stop_all_patterns()
    
    print("✅ Startup sequence completed!")

def speak_motivational_quote():
    """Speak the motivational quote"""
    speak_text(QUOTE)

# ------------------- WAIT FOR DECISION -------------------

def wait_for_user_decision(temp_file, led_connected):
    while True:
        if led_connected:
            start_listening_pattern()

        command = recognize_speech()
        if command:
            lower = command.lower()
            if "do the presentation" in lower:
                if led_connected:
                    start_speaking_pattern()
                send_gesture("handsup")
                try:
                    subprocess.run([sys.executable, "speakz_optimized.py", temp_file])
                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Could not run speakz_optimized.py: {e}")
                    speak_text("Sorry, there was an error with the presentation.")
                send_gesture("relax")
                break
            elif "goodbye" in lower or "bye" in lower:
                if led_connected:
                    start_speaking_pattern()
                send_gesture("handsdown")
                speak_text("Goodbye! Speakz is going to sleep.")
                if led_connected:
                    stop_all_patterns()
                break
            else:
                if led_connected:
                    start_speaking_pattern()
                send_gesture("handtogether")
                speak_text("I'm listening. Say 'Okay, do the presentation' or 'Goodbye'.")
                send_gesture("relax")

# ------------------- MAIN CONTROL -------------------

def main():
    print("Testing LED connection...")
    led_connected = test_connection()
    
    if led_connected:
        print("LED connection successful!")
    else:
        print("Warning: LED connection failed, continuing without LEDs")
    
    if led_connected:
        synchronized_startup()
    else:
        play_chime()
    
    print("Speaking motivational quote...")
    speak_motivational_quote()
    
    send_gesture("relax")
    print("🎤 Ready for voice commands!")

    while True:
        print("[WAITING] Say 'Hi' or 'Hey Speakz' to start.")
-
        if led_connected:
            start_listening_pattern()

        wake_input = recognize_speech()

        if wake_input and ("hi" in wake_input.lower() or "hey speakz" in wake_input.lower()):
            if led_connected:
                start_speaking_pattern()
            speak_greeting()
            
            # Use ask_practice to handle practice initiation
            ask_practice()

            # Check for optimized transcript and ask to present
            temp_file = "optimized_output.txt"
            if os.path.exists(temp_file):
                if led_connected:
                    start_speaking_pattern()
                send_gesture("handsup")
                speak_text("Would you like me to present the optimized speech now? Please say yes or no.")
                send_gesture("relax")

                if led_connected:
                    start_listening_pattern()
                response = recognize_speech()

                if response and "yes" in response.lower():
                    if led_connected:
                        start_speaking_pattern()
                    send_gesture("handsup")
                    try:
                        subprocess.run([sys.executable, "speakz_optimized.py", temp_file])
                    except subprocess.CalledProcessError as e:
                        print(f"[ERROR] Could not run speakz_optimized.py: {e}")
                        speak_text("Sorry, there was an error with the presentation.")
                    send_gesture("relax")
                elif response and "no" in response.lower():
                    if led_connected:
                        start_speaking_pattern()
                    speak_text("Okay, I'll wait. Just say 'Okay, do the presentation' or 'Goodbye'.")
                    wait_for_user_decision(temp_file, led_connected)
                else:
                    if led_connected:
                        start_speaking_pattern()
                    send_gesture("handtogether")
                    speak_text("I didn't catch that. Please say yes or no.")
                    send_gesture("relax")

        elif wake_input and ("goodbye" in wake_input.lower() or "exit" in wake_input.lower()):
            if led_connected:
                start_speaking_pattern()
            send_gesture("handsdown")
            speak_text("Goodbye! Speakz is going to sleep.")
            if led_connected:
                stop_all_patterns()
            break

        else:
            if led_connected:
                start_speaking_pattern()
            send_gesture("handtogether")
            speak_text("I'm listening. Say 'Hi' or 'Hey Speakz' to start.")
            send_gesture("relax")

        time.sleep(1)

# ------------------- RUN -------------------

if __name__ == "__main__":
    main()