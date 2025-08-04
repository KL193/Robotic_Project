# speak_azure.py

import azure.cognitiveservices.speech as speechsdk
import os
from colorama import Fore, init
from dotenv import load_dotenv

init(autoreset=True)
load_dotenv()

def speak_text(text: str):
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_SERVICE_REGION")

    if not speech_key or not service_region:
        print(Fore.RED + "Azure credentials not found in .env.")
        return

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"  # You can change the voice
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    print(Fore.GREEN + "🗣️ Speaking with Azure TTS...\n")
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(Fore.CYAN + "✅ Speech delivered.")
    else:
        print(Fore.RED + f"❌ Speech synthesis failed: {result.reason}")

if __name__ == "__main__":
    try:
        with open("optimized_transcript.txt", "r", encoding="utf-8") as f:
            optimized = f.read()
    except FileNotFoundError:
        print(Fore.RED + "❌ optimized_transcript.txt not found.")
        exit(1)

    speak_text(optimized)
