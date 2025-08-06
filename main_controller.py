import os
import subprocess
import sys
import time
from speakz_greeting import speak_text, recognize_speech, speak_greeting, update_practice_log
from gesture_sender import send_gesture
from led_controller import (start_startup_pattern, start_listening_pattern, 
                          start_speaking_pattern, start_processing_pattern, 
                          stop_all_patterns, test_connection)

def main():
    # Test LED connection first
    print("Testing LED connection...")
    led_connected = test_connection()
    
    if led_connected:
        # Start beautiful startup pattern for 40 seconds
        start_startup_pattern()
        print("🌈 Beautiful startup pattern running for 40 seconds...")
        time.sleep(10)  # Let the startup pattern run
    
    # Send initial relaxed gesture when starting
    send_gesture("relax")
    
    while True:
        print("[WAITING] Say 'Hi' or 'Hey Speakz' to start.")
        
        # Blue loading pattern while listening for wake word
        if led_connected:
            start_listening_pattern()
        
        wake_input = recognize_speech()
        
        if wake_input and ("hi" in wake_input.lower() or "hey speakz" in wake_input.lower()):
            # Purple pattern while robot is speaking greeting
            if led_connected:
                start_speaking_pattern()
            
            speak_greeting()
            
            # Add gesture while asking
            send_gesture("handsup")
            speak_text("Would you like to practice your presentation now? Please say yes or no.")
            send_gesture("relax")
            
            # Blue pattern while listening for response
            if led_connected:
                start_listening_pattern()
            
            response = recognize_speech()
            
            if response and "yes" in response.lower():
                count = update_practice_log()
                
                # Purple pattern while speaking
                if led_connected:
                    start_speaking_pattern()
                
                send_gesture("handsup")
                speak_text(f"This is your {count} time practicing today. Keep it up!")
                send_gesture("point")
                speak_text("Let's begin. Start your presentation after the beep.")
                send_gesture("relax")
                
                # Step 1: Record, Analyze, and provide feedback
                try:
                    subprocess.run([sys.executable, "live_transcription.py"], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Could not run live_transcription.py: {e}")
                    if led_connected:
                        start_speaking_pattern()
                    speak_text("Sorry, there was an error with the recording.")
                    continue
                
                # Step 2: Read optimized text from file
                temp_file = "optimized_output.txt"
                if not os.path.exists(temp_file):
                    if led_connected:
                        start_speaking_pattern()
                    send_gesture("handsdown")
                    speak_text("Sorry, I couldn't find the optimized transcript.")
                    continue
                
                with open(temp_file, "r", encoding="utf-8") as f:
                    optimized_text = f.read()
                
                # Step 3: Ask if user wants the optimized speech presented
                if led_connected:
                    start_speaking_pattern()
                
                send_gesture("handsup")
                speak_text("Would you like me to present the optimized speech now? Please say yes or no.")
                send_gesture("relax")
                
                # Blue pattern while listening
                if led_connected:
                    start_listening_pattern()
                
                answer = recognize_speech()
                
                if answer and "yes" in answer.lower():
                    # Purple pattern while delivering optimized speech
                    if led_connected:
                        start_speaking_pattern()
                    
                    send_gesture("handsup")
                    try:
                        subprocess.run([sys.executable, "speakz_optimized.py", temp_file])
                    except subprocess.CalledProcessError as e:
                        print(f"[ERROR] Could not run speakz_optimized.py: {e}")
                        speak_text("Sorry, there was an error with the presentation.")
                    send_gesture("relax")
                else:
                    if led_connected:
                        start_speaking_pattern()
                    speak_text("Okay, I'll wait. Just say 'Okay, do the presentation' or say 'Goodbye' to stop.")
                    wait_for_user_decision(temp_file, led_connected)
            
            elif response and "no" in response.lower():
                if led_connected:
                    start_speaking_pattern()
                send_gesture("handsdown")
                speak_text("Alright! Just say 'Hey Speakz' again when you're ready.")
                send_gesture("relax")
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
            
            # Turn off all LEDs when going to sleep
            if led_connected:
                stop_all_patterns()
            break
        
        time.sleep(1)

def wait_for_user_decision(temp_file, led_connected):
    while True:
        # Blue pattern while waiting for command
        if led_connected:
            start_listening_pattern()
            
        command = recognize_speech()
        if command:
            lower = command.lower()
            if "do the presentation" in lower:
                # Purple pattern while delivering optimized speech
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
            elif "goodbye" in lower or "exit" in lower:
                if led_connected:
                    start_speaking_pattern()
                send_gesture("handsdown")
                speak_text("Goodbye! Speakz is going to sleep.")
                
                # Turn off all LEDs when going to sleep
                if led_connected:
                    stop_all_patterns()
                break
            else:
                if led_connected:
                    start_speaking_pattern()
                send_gesture("handtogether")
                speak_text("I'm listening. Say 'Okay, do the presentation' or 'Goodbye'.")
                send_gesture("relax")

if __name__ == "__main__":
    main()