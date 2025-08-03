# speak_optimized.py
import azure.cognitiveservices.speech as speechsdk

speech_key = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
service_region = "eastus"  # e.g., "eastus"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"

def speak_text(text):
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("[INFO] Spoke final optimized text.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"[ERROR] TTS canceled: {cancellation.reason}")
        if cancellation.error_details:
            print(f"[DETAILS] {cancellation.error_details}")

if __name__ == "__main__":
    with open("optimized_transcript.txt", "r") as f:
        final_text = f.read()
    speak_text(final_text)
