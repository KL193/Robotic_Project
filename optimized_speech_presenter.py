import azure.cognitiveservices.speech as speechsdk
import time
from datetime import datetime

# Replace with your Azure credentials
AZURE_KEY = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
AZURE_REGION = "eastus"

def speak_text(text, voice_name="en-US-GuyNeural"):
    """
    Speaks given text using Azure TTS.
    """
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
    speech_config.speech_synthesis_voice_name = voice_name
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    print(f"[Robot] Speaking with voice: {voice_name}")
    synthesizer.speak_text_async(text).get()
    print("[Robot] Done speaking.")

def greet_user():
    """
    Greets the user based on current time.
    """
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greet = "Good morning!"
    elif 12 <= hour < 17:
        greet = "Good afternoon!"
    elif 17 <= hour < 21:
        greet = "Good evening!"
    else:
        greet = "Hello!"

    speak_text(f"{greet} I'm your speech coach robot. I will now present your improved speech.")

def get_optimized_script(original_script):
    """
    Cleans the script by removing filler words.
    """
    filler_words = {
        "um", "uh", "like", "you know", "I mean", "actually", "basically",
        "so", "well", "kind of", "sort of", "literally", "just", "okay", "right"
    }

    # Basic cleaning
    words = original_script.split()
    cleaned_words = [word for word in words if word.lower() not in filler_words]
    return " ".join(cleaned_words)

def main():
    # Replace this with dynamic script (from analysis stage)
    original_script = """
    good morning all of you today I am going to present about our project proposal called Speakz like you know I mean we are going to actually use enhanced live transcription in a presentation practice robot with real time feedback and analysis
    """

    greet_user()
    time.sleep(1)

    optimized_script = get_optimized_script(original_script)

    speak_text("Here is your optimized version:")
    time.sleep(1)
    speak_text(optimized_script)

if __name__ == "__main__":
    main()
