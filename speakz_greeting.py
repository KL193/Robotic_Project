import azure.cognitiveservices.speech as speechsdk
from datetime import datetime

# Replace with your Azure credentials
speech_key = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
service_region = "eastus"  # Example: eastus, westeurope etc.

# Set up Azure Speech Config
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"

def speak_text(text):
    """Convert text to speech using Azure."""
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("[INFO] Text spoken successfully.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"[ERROR] Speech synthesis canceled: {cancellation.reason}")
        if cancellation.error_details:
            print(f"[DETAILS] {cancellation.error_details}")

def recognize_speech():
    """Recognize one short phrase from microphone input."""
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("[LISTENING] Please speak now...")
    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"[RECOGNIZED] {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("[ERROR] No speech could be recognized.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"[ERROR] Recognition canceled: {cancellation.reason}")
        if cancellation.error_details:
            print(f"[DETAILS] {cancellation.error_details}")
    return None

def speak_greeting():
    """Speak a time-based greeting."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting_text = "Good morning, I'm Speakz!"
    elif 12 <= hour < 17:
        greeting_text = "Good afternoon, I'm Speakz!"
    else:
        greeting_text = "Good evening, I'm Speakz!"
    speak_text(f"{greeting_text} Ready to help with your presentation.")

def ask_practice():
    """Ask the user if they want to start practicing."""
    speak_text("Would you like to practice your presentation now? Please say yes or no.")
    response = recognize_speech()
    print(f"[USER SAID] {response}")
    
    if response and "yes" in response.lower():
        speak_text("Great! Let's begin. Please start your presentation after the beep.")
        record_and_analyze()
    elif response and "no" in response.lower():
        speak_text("Okay! Let me know whenever you're ready.")
    else:
        speak_text("Sorry, I didn't catch that. Please say yes or no next time.")

def record_and_analyze():
    """Placeholder for voice analysis module."""
    speak_text("Recording your presentation... This feature will be implemented next.")

# Run the program
if __name__ == "__main__":
    speak_greeting()
    ask_practice()
