import azure.cognitiveservices.speech as speechsdk
#from gesture_sender import send_gesture
from datetime import datetime
import subprocess
import os
import sys
import time

# ==== Azure Speech Config ====
speech_key = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
service_region = "eastus"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"

LOG_FILE = "practice_log.txt"

# ==== Speak Text ====
def speak_text(text):
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("[ERROR] Speech synthesis failed.")

# ==== Recognize One Speech ====
def recognize_speech():
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    print("[LISTENING] Please speak now...")
    result = recognizer.recognize_once_async().get()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"[RECOGNIZED] {result.text}")
        return result.text
    return None

# ==== Time-based Greeting ====
def speak_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
       # send_gesture("hands_up")
        speak_text( "Good morning! I'm Speakz, your presentation buddy. How can I help you today?")
    elif 12 <= hour < 17:
        #send_gesture("hands_up")
        speak_text( "Good afternoon! I'm Speakz, your presentation buddy. How can I help you today?")
       
    else:
        #send_gesture("hands_up")
        speak_text( "Good evening! I'm Speakz, your presentation buddy. How can I help you today?")
   # speak_text(f"{greeting_text} I'm Speakz, your presentation buddy. How can I help you today?")

# ==== Track Daily Practice Progress ====
def update_practice_log():
    today = datetime.now().strftime("%Y-%m-%d")
    log_data = {}

    # Read existing log
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                date, count = line.strip().split(": ")
                log_data[date] = int(count)

    # Update today's count
    log_data[today] = log_data.get(today, 0) + 1

    # Save updated log
    with open(LOG_FILE, "w") as f:
        for date, count in log_data.items():
            f.write(f"{date}: {count}\n")

    return log_data[today]

# ==== Call Presentation Recording Script ====
def record_and_analyze():
    try:
        print("[INFO] Launching live_transcription.py...")
        script_path = os.path.join(os.path.dirname(__file__), "live_transcription.py")
        subprocess.run([sys.executable, script_path], check=True)
        print("[INFO] Recording and analysis finished.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Could not run script: {e}")

# ==== Ask to Practice with Retry Loop ====
def ask_practice():
    """Ask user until they say yes or no."""
    while True:
        speak_text("Would you like to practice your presentation now? Please say yes or no.")
        response = recognize_speech()

        if response:
            lower_response = response.lower()
            if "yes" in lower_response:
                count = update_practice_log()
              
                speak_text(f"This is your {count}  time practicing today. Keep it up!")
                speak_text("Let's begin. Start your presentation after the beep.")
                record_and_analyze()
                break

            elif "no" in lower_response:
                speak_text("Alright! Just say 'Hi' again when you're ready.")
                break
            else:
                speak_text("Sorry, I didn't get that. Please say yes or no.")
       # else:
         #   speak_text("I didn't hear anything. Please try again.")

# ==== Wake Word Loop ====
def listen_for_wake_word():
    while True:
        #send_gesture("hands_up")
        print("[WAITING] Say 'Hi' or 'Hey Speakz' to start.")
        spoken_text = recognize_speech()

        if spoken_text:
            lower_text = spoken_text.lower()

            if "hi" in lower_text or "hey speakz" in lower_text:
                speak_greeting()
                ask_practice()

            elif "goodbye" in lower_text or "exit" in lower_text:
                speak_text("Goodbye! Have a great day.")
                break

            else:
                speak_text("I'm listening. Just say 'Hi' or 'Hey Speakz' to start.")
       # else:
           # speak_text("I didn't hear anything. Try saying 'Hi Spakz'.")
        
        time.sleep(1)


# ==== Entry Point ====
if __name__ == "__main__":
    listen_for_wake_word()
