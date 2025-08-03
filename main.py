# main.py

from live_transcription import transcribe_audio
from optimized_speech_presenter import optimize_text
from speakz_greeting import speak_text


def main():
    print("🔴 Step 1: Transcribing recorded speech...")
    raw_transcript = transcribe_audio("recording.wav")
    print(f"📄 Raw Transcript:\n{raw_transcript}")

    print("\n🧠 Step 2: Optimizing the speech...")
    optimized_transcript = optimize_text(raw_transcript)
    print(f"✍️ Optimized Transcript:\n{optimized_transcript}")

    print("\n🔊 Step 3: Converting optimized speech to voice...")
    text_to_speech(optimized_transcript, output_file="recording_clean.wav")
    print("✅ Done! Optimized speech saved as recording_clean.wav")

if __name__ == "__main__":
    main()
