import azure.cognitiveservices.speech as speechsdk
from datetime import datetime
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import time
import google.generativeai as genai
from colorama import Fore, init

# ============ INIT ============
init(autoreset=True)

# ============ Azure Speech Config ============
speech_key = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
service_region = "eastus"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"
speech_config.speech_recognition_language = "en-IN"

# ============ Gemini Config ============
genai.configure(api_key="AIzaSyDGrPwtilNwNz2bdoG2TH7Dq6f-7uBvRZE")  # Replace with your key
gemini_model = genai.GenerativeModel("gemini-1.5-pro-latest")

# ============ Filler Words ============
filler_words = {
    "um", "uh", "er", "ah", "hmm", "like", "you know", "i mean", "basically", "actually", "literally", "just",
    "so", "well", "okay", "right", "alright", "kind of", "sort of", "you see", "you get me", "you feel me",
    "anyway", "stuff like that", "things like that"
}

# ============ Core Functions ============

def speak_text(text):
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("[INFO] Text spoken successfully.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"[ERROR] Speech synthesis canceled: {cancellation.reason}")
        if cancellation.error_details:
            print(f"[DETAILS] {cancellation.error_details}")

def speak_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting_text = "Good morning, I'm Speakz!"
    elif 12 <= hour < 17:
        greeting_text = "Good afternoon, I'm Speakz!"
    else:
        greeting_text = "Good evening, I'm Speakz!"
    speak_text(f"{greeting_text} Ready to help with your presentation.")

def record_audio(filename="recording.wav", duration=20, sample_rate=44100):
    print(Fore.CYAN + "🎤 Recording started... Speak now!")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    audio_int16 = np.int16(audio * 32767)
    wav.write(filename, sample_rate, audio_int16)
    print(Fore.CYAN + "✅ Recording saved.")
    return filename, audio_int16.flatten(), sample_rate

def transcribe_audio(filename):
    audio_config = speechsdk.audio.AudioConfig(filename=filename)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(Fore.GREEN + f"Transcription: {result.text}")
        with open("transcript.txt", "w") as f:
            f.write(result.text.strip())
        return result.text.strip()
    else:
        print(Fore.RED + "[ERROR] Transcription failed.")
        return ""

def analyze_transcript(text):
    words = text.lower().split()
    filler_count = sum(word in filler_words for word in words)
    print(Fore.YELLOW + f"Detected filler words: {filler_count}")

def optimize_text(original_text):
    prompt = f"""
    You are a helpful speaking coach. Rewrite the following transcript to sound more professional and polished.
    Remove filler words like 'um', 'like', 'you know', and improve clarity and grammar.

    Original Transcript:
    \"\"\"{original_text}\"\"\"
    """

    try:
        response = gemini_model.generate_content(prompt)
        optimized_text = response.text.strip()
        with open("optimized_transcript.txt", "w") as f:
            f.write(optimized_text)
        print(Fore.GREEN + "✅ Optimized transcript generated.")
        return optimized_text
    except Exception as e:
        print(Fore.RED + f"[ERROR] Gemini optimization failed: {e}")
        return original_text

def speak_optimized():
    if os.path.exists("optimized_transcript.txt"):
        with open("optimized_transcript.txt", "r") as f:
            final_text = f.read()
        speak_text(final_text)
    else:
        print(Fore.RED + "Optimized transcript file not found.")

# ============ Main Workflow ============
if __name__ == "__main__":
    speak_greeting()
    speak_text("Would you like to practice your presentation now? Please say yes or no.")
    print("[SIMULATING INPUT] --> Yes")
    speak_text("Great! Let's begin. Please start your presentation after the beep.")

    filename, _, _ = record_audio()
    transcript = transcribe_audio(filename)

    if transcript:
        analyze_transcript(transcript)
        optimized = optimize_text(transcript)
        speak_optimized()
    else:
        speak_text("Sorry, I couldn't understand your speech. Please try again.")
