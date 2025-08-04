import azure.cognitiveservices.speech as speechsdk
import sys
import os

# ==== Azure Speech Config ====
speech_key = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
service_region = "eastus"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"  # Change voice if needed

def deliver_speech(text: str):
    """Speak the given text using Azure TTS."""
    if not text.strip():
        print("[ERROR] No text provided to speak.")
        return

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("[SUCCESS] Speech delivered successfully.")
    else:
        print("[ERROR] Speech synthesis failed.")
        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"[CANCELED] Reason: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                print(f"[ERROR] Details: {cancellation.error_details}")

if __name__ == "__main__":
    # Optional: Read optimized text from a file
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        if os.path.exists(input_path):
            with open(input_path, "r", encoding="utf-8") as f:
                optimized_text = f.read()
            deliver_speech(optimized_text)
        else:
            print(f"[ERROR] File not found: {input_path}")
    else:
        # Or enter manually for testing
        print("Enter the optimized speech below. Press Enter when done:")
        optimized_text = sys.stdin.read()
        deliver_speech(optimized_text)
