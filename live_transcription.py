import sys
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import time
from colorama import Fore, init
import speech_recognition as sr

init(autoreset=True)

duration = 20
sample_rate = 44100
threshold_volume = 0.01
pause_threshold_sec = 0.3

filler_words = {
    "um", "uh", "er", "ah", "hmm",
    "like", "you know", "i mean",
    "basically", "actually", "literally",
    "just", "so", "well", "okay",
    "right", "alright", "kind of", "sort of",
    "you see", "you get me", "you feel me",
    "anyway", "stuff like that", "things like that"
}

def simulate_led(color, message):
    color_map = {
        "green": Fore.GREEN,
        "red": Fore.RED,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "white": Fore.WHITE
    }
    print(color_map.get(color.lower(), Fore.WHITE) + f"[LED] {message}")
    time.sleep(0.3)

def blink_led(color, times=3):
    for _ in range(times):
        simulate_led(color, "●")
        print(" ", end="\r")
        time.sleep(0.2)

def record_audio(filename="recording.wav"):
    print(Fore.CYAN + "🎤 Recording started... Speak now!")
    simulate_led("blue", "Listening...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    audio_int16 = np.int16(audio * 32767)
    wav.write(filename, sample_rate, audio_int16)
    print(Fore.CYAN + "✅ Recording saved.")
    return filename, audio_int16.flatten()

def transcribe_audio(filename):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data)
        print(Fore.WHITE + f"\n🗣️ Transcription: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print(Fore.RED + "❌ Speech was unintelligible.")
        return ""
    except sr.RequestError as e:
        print(Fore.RED + f"❌ Could not request results from Google Speech Recognition service; {e}")
        return ""

def analyze_audio(audio_data):
    if audio_data.dtype == np.int16 or audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 32767

    volume = np.abs(audio_data).mean()
    duration_secs = len(audio_data) / sample_rate
    silence_ratio = np.sum(np.abs(audio_data) < threshold_volume) / len(audio_data)

    print(Fore.WHITE + f"\n🔍 Duration: {duration_secs:.2f} sec | Avg Volume: {volume:.5f} | Silence: {silence_ratio:.2%}")

    if volume > 0.05:
        simulate_led("red", "⚠️ Too loud!")
    elif volume < 0.005:
        simulate_led("red", "⚠️ Too soft or silent")
    else:
        simulate_led("green", "✅ Volume is good")

    frame_size = int(sample_rate * 0.05)
    silent_frames = np.abs(audio_data) < threshold_volume
    pauses = 0
    pause_durations = []

    start_pause = None
    for i in range(0, len(audio_data), frame_size):
        frame = silent_frames[i:i+frame_size]
        if np.all(frame):
            if start_pause is None:
                start_pause = i
        else:
            if start_pause is not None:
                pause_length_sec = (i - start_pause) / sample_rate
                if pause_length_sec >= pause_threshold_sec:
                    pauses += 1
                    pause_durations.append(pause_length_sec)
                start_pause = None
    if start_pause is not None:
        pause_length_sec = (len(audio_data) - start_pause) / sample_rate
        if pause_length_sec >= pause_threshold_sec:
            pauses += 1
            pause_durations.append(pause_length_sec)

    if pauses > 3:
        blink_led("yellow", times=3)
        print(Fore.YELLOW + f"⚠️ Too many pauses detected: {pauses}")
    elif pauses > 0:
        simulate_led("yellow", f"🙂 Pauses: {pauses}")
    else:
        simulate_led("green", "👍 No significant pauses")

    return pauses, pause_durations

def analyze_transcript(text, duration_secs, pauses):
    if not text:
        print(Fore.RED + "No transcript to analyze for filler words or speech speed.")
        return

    words = text.split()
    total_words = len(words)
    filler_count_map = {fw: words.count(fw) for fw in filler_words if fw in words}
    total_filler_count = sum(filler_count_map.values())

    effective_speaking_time = max(duration_secs - pauses * pause_threshold_sec, 0.1)
    speech_speed_wpm = (total_words / effective_speaking_time) * 60

    print(Fore.WHITE + f"\n🧠 Filler words detected: {total_filler_count} ({(total_filler_count / total_words) * 100:.2f}%)")

    if filler_count_map:
        print(Fore.YELLOW + "🔍 Filler Word Breakdown:")
        for word, count in filler_count_map.items():
            print(f"   - '{word}': {count} time(s)")

    print(Fore.WHITE + f"\n🚀 Speech Speed: {speech_speed_wpm:.1f} words per minute")

    if total_filler_count > 3:
        simulate_led("red", "⚠️ Too many filler words")
    else:
        simulate_led("green", "✅ Good filler word usage")

    if speech_speed_wpm < 100:
        simulate_led("yellow", "⚠️ Speech is too slow")
    elif speech_speed_wpm > 160:
        simulate_led("yellow", "⚠️ Speech is too fast")
    else:
        simulate_led("green", "✅ Speech speed is good")

if __name__ == "__main__":
    filename, audio = record_audio()
    pauses, pause_durations = analyze_audio(audio)
    transcript = transcribe_audio(filename)
    analyze_transcript(transcript, duration, pauses)
