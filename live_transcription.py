import sys
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import time
import os
import datetime
from colorama import Fore, init
import speech_recognition as sr
from gemini_optimize import optimize_presentation_script
from speakz_greeting import speak_text, speak_with_gesture
from led_controller import led_good, led_too_loud, led_too_soft, led_long_pause, led_off, test_connection, start_processing_pattern
import random
import pygame

init(autoreset=True)

# ===== CONFIG =====
duration = 40
sample_rate = 44100
threshold_db_good_min = 60
threshold_db_good_max = 80
threshold_db_soft = 55
threshold_db_loud = 85
pause_threshold_sec = 1.0
realtime_pause_threshold = 2.0
CHIME_AUDIO_FILE = "waiting.mp3"  # Reuses main_controller.py chime

filler_words = {
    "um", "uh", "er", "ah", "hmm",
    "like", "you know", "i mean",
    "basically", "actually", "literally",
    "just", "so", "well", "okay",
    "right", "alright", "kind of", "sort of",
    "you see", "you get me", "you feel me",
    "anyway", "stuff like that", "things like that"
}

# Feedback message variations
VOLUME_GOOD = [
    "Great volume at {volume:.1f} decibel! You're hitting the sweet spot!",
    "Your voice was perfect at {volume:.1f} decibel, keep it up!",
    "Awesome clarity at {volume:.1f} decibel, well done!"
]
VOLUME_LOUD = [
    "Whoa, your volume was a booming {volume:.1f} decibel! Try softening it a bit.",
    "Your voice was loud at {volume:.1f} decibel! Speak a tad quieter for comfort.",
    "Powerful delivery at {volume:.1f} decibel! Tone it down slightly for balance."
]
VOLUME_SOFT = [
    "Your volume was a bit low at {volume:.1f} decibel. Project more to shine!",
    "A bit quiet at {volume:.1f} decibel! Speak up to grab attention.",
    "Your voice was soft at {volume:.1f} decibel. Boost it for clarity!"
]
PAUSE_MANY = [
    "You had {pauses} long pauses, which may disrupt flow. Try keeping pauses brief.",
    "{pauses} long pauses detected. Shorten them for a smoother delivery!",
    "With {pauses} pauses, your speech felt choppy. Aim for briefer pauses."
]
PAUSE_FEW = [
    "Your {pauses} pause(s) added great emphasis, nice work!",
    "{pauses} pause(s) gave your speech nice rhythm, well done!",
    "Good use of {pauses} pause(s) to highlight key points!"
]
PAUSE_NONE = [
    "Smooth delivery with no long pauses, fantastic!",
    "You kept the flow going with zero long pauses, great job!",
    "No unnecessary pauses, your speech was fluid and engaging!"
]
FILLER_MANY = [
    "You used {total_filler_count} filler words ({percent:.1f}%). Try cutting back for polish: {fillers}.",
    "{total_filler_count} fillers ({percent:.1f}%) slipped in. Reduce them for a crisp delivery: {fillers}.",
    "Your speech had {total_filler_count} fillers ({percent:.1f}%). Skip some for a smoother flow: {fillers}."
]
FILLER_OK = [
    "Nice job with just {total_filler_count} filler words, that’s great for natural speech!",
    "Only {total_filler_count} fillers, you’re keeping it clean and clear!",
    "Great work with minimal fillers ({total_filler_count}), your speech flows well!"
]
SPEED_SLOW = [
    "Your pace was slow at {speech_speed_wpm:.1f} WPM. Speed up a bit to keep the energy high!",
    "A bit leisurely at {speech_speed_wpm:.1f} WPM. Try a faster pace for engagement.",
    "Your speed was {speech_speed_wpm:.1f} WPM. Pick up the tempo slightly!"
]
SPEED_FAST = [
    "Your pace was fast at {speech_speed_wpm:.1f} WPM. Slow down for better clarity!",
    "Zooming at {speech_speed_wpm:.1f} WPM! Ease up to let your words sink in.",
    "Rapid fire at {speech_speed_wpm:.1f} WPM! Try a slower pace for impact."
]
SPEED_OK = [
    "Perfect pace at {speech_speed_wpm:.1f} WPM, you’re spot on!",
    "Great speed of {speech_speed_wpm:.1f} WPM, keeping the audience hooked!",
    "Your {speech_speed_wpm:.1f} WPM pace was ideal, well done!"
]
WRAP_UP = [
    "Great effort! Let’s keep polishing your presentation skills!",
    "Awesome session! Ready to take your speech to the next level?",
    "Fantastic work! Let’s make your next practice even better!"
]
ACTIONABLE_TIPS = [
   # "Try pausing briefly instead of saying ‘um’ or ‘uh’ for a polished delivery.",
    "Practice projecting your voice to hit that ideal volume range.",
    "Aim for a steady pace to keep your audience engaged throughout.",
    "Use short pauses to emphasize key points without breaking the flow."
]

# Global variables for real-time analysis
led_connected = False
silence_start_time = None
audio_buffer = []
last_led_time = 0
led_cooldown_sec = 0.1
last_led_state = None

def amplitude_to_db(amplitude):
    return 20 * np.log10(np.abs(amplitude) + 1e-10) + 90

def check_led_connection():
    global led_connected
    led_connected = test_connection()
    if not led_connected:
        print(Fore.YELLOW + "[WARNING] ESP32 not connected. LEDs will not work.")
    return led_connected

def save_user_transcript_copy(optimized_text, original_transcript):
    try:
        user_transcripts_folder = r"D:\uoj\4 th year\Robotics\Speakz-Greetings\Robotic_Project\User_Transcripts"
        os.makedirs(user_transcripts_folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        user_filename = f"presentation_session_{timestamp}.txt"
        user_file_path = os.path.join(user_transcripts_folder, user_filename)
        
        session_content = f"""SPEAKZ PRESENTATION SESSION REPORT
{'='*50}
Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Session ID: {timestamp}

ORIGINAL TRANSCRIPT:
{'-'*20}
{original_transcript}

OPTIMIZED VERSION:
{'-'*17}
{optimized_text}

{'='*50}
End of Session Report
"""
        with open(user_file_path, "w", encoding="utf-8") as f:
            f.write(session_content)
        print(Fore.CYAN + f"💾 User session saved to: User_Transcripts/{user_filename}")
        return user_file_path
    except Exception as e:
        print(Fore.YELLOW + f"⚠️ Warning: Could not save user transcript copy: {e}")
        return None

def update_led_realtime(chunk):
    global silence_start_time, led_connected, last_led_time, last_led_state

    if not led_connected:
        return

    if chunk.dtype == np.int16 or chunk.dtype == np.int32:
        chunk = chunk.astype(np.float32) / 32767

    volume = amplitude_to_db(np.abs(chunk).mean())
    is_silence = volume < threshold_db_soft

    now = time.time()
    if now - last_led_time < led_cooldown_sec:
        return

    current_led_state = None

    if is_silence:
        if silence_start_time is None:
            silence_start_time = now
        else:
            silence_duration = now - silence_start_time
            if silence_duration > realtime_pause_threshold:
                current_led_state = "long_pause"
    else:
        silence_start_time = None

        if volume > threshold_db_loud:
            current_led_state = "too_loud"
        elif volume < threshold_db_soft:
            current_led_state = "too_soft"
        else:
            current_led_state = "good"

    if current_led_state and current_led_state != last_led_state:
        try:
            if current_led_state == "good":
                led_good()
            elif current_led_state == "too_loud":
                led_too_loud()
            elif current_led_state == "too_soft":
                led_too_soft()
            elif current_led_state == "long_pause":
                led_long_pause()
            last_led_state = current_led_state
            last_led_time = now
            print(f"\r[LED] Volume: {volume:.1f} dB -> {current_led_state}         ", end="", flush=True)
        except Exception as e:
            print(f"\n[LED ERROR] {e}")

def audio_callback(indata, frames, time, status):
    global audio_buffer
    if status:
        print(f'Audio callback error: {status}')
    audio_buffer.append(indata.copy())
    chunk = indata.flatten()
    update_led_realtime(chunk)
    volume = amplitude_to_db(np.abs(chunk).mean())
    print(f"\r{Fore.CYAN}🎤 Recording... Vol: {volume:.1f} dB   ", end="", flush=True)

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

def play_feedback_chime():
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(CHIME_AUDIO_FILE)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print(f"[WARNING] Could not play feedback chime: {e}")

def transcribe_audio(filename, max_retries=3):
    recognizer = sr.Recognizer()
    retries = 0
    
    while retries < max_retries:
        with sr.AudioFile(filename) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            print(Fore.WHITE + f"\n🗣️ Transcription: {text}")
            return text.lower()
        except sr.UnknownValueError:
            retries += 1
            print(Fore.YELLOW + f"[WARNING] Speech unintelligible. {max_retries - retries} retries left.")
            if retries < max_retries:
                speak_with_gesture(random.choice([
                    "My ears are on strike! Try speaking clearly one more time!",
                    "Whoops, I missed that! Please record again clearly!",
                   # "My circuits are confused! One more try, please!"
                ]), "handtogether")
        except sr.RequestError as e:
            print(Fore.RED + f"❌ Google Speech error: {e}")
            return ""
    
    print(Fore.YELLOW + "[INFO] Max retries reached. Please type your transcript.")
    return input("Type your transcript: ").lower()

def record_audio(filename="recording.wav"):
    global audio_buffer, led_connected, silence_start_time, last_led_time, last_led_state
    audio_buffer = []
    silence_start_time = None
    last_led_time = 0
    last_led_state = None
    
    check_led_connection()
    print(Fore.CYAN + "🎤 Recording started with real-time LED feedback...")
    if led_connected:
        print(Fore.WHITE + "Green = Good | Red = Too loud/Long pause | Orange = Too soft")
    else:
        print(Fore.YELLOW + "LED feedback disabled (ESP32 not connected)")
    
    simulate_led("blue", "Listening...")
    
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, 
                          callback=audio_callback, dtype='float32'):
            sd.sleep(int(duration * 1000))
    except Exception as e:
        print(f"\n{Fore.RED}Recording error: {e}")
        return None, None
    
    if led_connected:
        led_off()
    
    print(f"\n{Fore.CYAN}✅ Recording complete!")
    
    if audio_buffer:
        audio = np.concatenate(audio_buffer, axis=0).flatten()
        audio_int16 = np.int16(audio * 32767)
        wav.write(filename, sample_rate, audio_int16)
        print(Fore.CYAN + "💾 Recording saved.")
        return filename, audio_int16.flatten()
    else:
        print(Fore.RED + "❌ No audio recorded!")
        return None, None

def analyze_audio(audio_data):
    if audio_data.dtype == np.int16 or audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 32767

    volume = amplitude_to_db(np.abs(audio_data).mean())
    duration_secs = len(audio_data) / sample_rate
    silence_ratio = np.sum(amplitude_to_db(np.abs(audio_data)) < threshold_db_soft) / len(audio_data)

    print(Fore.WHITE + f"\n🔍 Duration: {duration_secs:.2f} sec | Avg Volume: {volume:.1f} dB | Silence: {silence_ratio:.2%}")

    if volume > threshold_db_loud:
        simulate_led("red", "⚠️ Too loud!")
    elif volume < threshold_db_soft:
        simulate_led("red", "⚠️ Too soft or silent")
    else:
        simulate_led("green", "✅ Volume is good")

    frame_size = int(sample_rate * 0.05)
    silent_frames = amplitude_to_db(np.abs(audio_data)) < threshold_db_soft
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

    if pauses > 5:
        blink_led("yellow", times=3)
        print(Fore.YELLOW + f"⚠️ Too many pauses detected: {pauses}")
    elif pauses > 0:
        simulate_led("yellow", f"🙂 Pauses: {pauses}")
    else:
        simulate_led("green", "👍 No significant pauses")

    return pauses, pause_durations

def analyze_transcript(text, duration_secs, pauses):
    if not text:
        print(Fore.RED + "No transcript to analyze.")
        return None

    words = text.split()
    total_words = len(words)
    filler_count_map = {fw: words.count(fw) for fw in filler_words if fw in words}
    total_filler_count = sum(filler_count_map.values())

    effective_time = max(duration_secs - pauses * pause_threshold_sec, 0.1)
    speech_speed_wpm = (total_words / effective_time) * 60

    print(Fore.WHITE + f"\n🧠 Filler words: {total_filler_count} ({(total_filler_count / total_words) * 100:.2f}%)")
    if filler_count_map:
        print(Fore.YELLOW + "🔍 Filler Word Breakdown:")
        for word, count in filler_count_map.items():
            print(f"   - '{word}': {count}x")

    print(Fore.WHITE + f"\n🚀 Speech Speed: {speech_speed_wpm:.1f} words/min")

    if total_filler_count > 3:
        simulate_led("red", "⚠️ Too many filler words")
    else:
        simulate_led("green", "✅ Filler usage okay")

    if speech_speed_wpm < 120:
        simulate_led("yellow", "⚠️ Too slow")
    elif speech_speed_wpm > 150:
        simulate_led("yellow", "⚠️ Too fast")
    else:
        simulate_led("green", "✅ Speed okay")

    return {
        "filler_count_map": filler_count_map,
        "total_filler_count": total_filler_count,
        "total_words": total_words,
        "speech_speed_wpm": speech_speed_wpm
    }

def generate_feedback_summary(volume, pauses, pause_durations, filler_count_map, total_filler_count, total_words, speech_speed_wpm):
    feedback_lines = []
    
    # Volume feedback
    if volume > threshold_db_loud:
        feedback_lines.append(random.choice(VOLUME_LOUD).format(volume=volume))
    elif volume < threshold_db_soft:
        feedback_lines.append(random.choice(VOLUME_SOFT).format(volume=volume))
    else:
        feedback_lines.append(random.choice(VOLUME_GOOD).format(volume=volume))
    
    # Pause feedback
    if pauses > 5:
        feedback_lines.append(random.choice(PAUSE_MANY).format(pauses=pauses))
    elif pauses > 0:
        feedback_lines.append(random.choice(PAUSE_FEW).format(pauses=pauses))
    else:
        feedback_lines.append(random.choice(PAUSE_NONE))
    
    # Filler feedback
    if total_filler_count > 0:
        percent = (total_filler_count / total_words) * 100 if total_words > 0 else 0
        fillers = ", ".join(f"'{k}' ({v})" for k, v in filler_count_map.items())
        if total_filler_count > 3:
            feedback_lines.append(random.choice(FILLER_MANY).format(total_filler_count=total_filler_count, percent=percent, fillers=fillers))
        else:
            feedback_lines.append(random.choice(FILLER_OK).format(total_filler_count=total_filler_count))
    else:
        feedback_lines.append(random.choice(FILLER_OK).format(total_filler_count=0))
    
    # Speed feedback
    if speech_speed_wpm < 120:
        feedback_lines.append(random.choice(SPEED_SLOW).format(speech_speed_wpm=speech_speed_wpm))
    elif speech_speed_wpm > 150:
        feedback_lines.append(random.choice(SPEED_FAST).format(speech_speed_wpm=speech_speed_wpm))
    else:
        feedback_lines.append(random.choice(SPEED_OK).format(speech_speed_wpm=speech_speed_wpm))
    
    # Select actionable tip based on weakest metric
    weaknesses = []
    if volume > threshold_db_loud or volume < threshold_db_soft:
        weaknesses.append("volume")
    if pauses > 5:
        weaknesses.append("pauses")
    if total_filler_count > 3:
        weaknesses.append("fillers")
    if speech_speed_wpm < 120 or speech_speed_wpm > 150:
        weaknesses.append("speed")
    
    tip = random.choice(ACTIONABLE_TIPS)
    if weaknesses:
        weak_area = random.choice(weaknesses)
        if weak_area == "volume":
            tip = "Practice projecting your voice to hit that ideal volume range."
        elif weak_area == "pauses":
            tip = "Use short pauses to emphasize key points without breaking the flow."
      #  elif weak_area == "fillers":
       #     tip = "Try pausing briefly instead of saying ‘um’ or ‘uh’ for a polished delivery."
        elif weak_area == "speed":
            tip = "Aim for a steady pace to keep your audience engaged throughout."
    
    feedback_lines.append(random.choice(WRAP_UP))
    feedback_lines.append(tip)
    
    return feedback_lines

if __name__ == "__main__":
    print(Fore.CYAN + "🤖 Starting Speech Analysis with LED Feedback System")
    print(Fore.WHITE + "=" * 60)
    
    filename, audio = record_audio()
    
    if filename and audio is not None:
        pauses, pause_durations = analyze_audio(audio)
        transcript = transcribe_audio(filename)
        transcript_analysis = analyze_transcript(transcript, duration, pauses)

        if transcript and transcript_analysis:
            volume = amplitude_to_db(np.abs(audio).mean())
            feedback_lines = generate_feedback_summary(
                volume=volume,
                pauses=pauses,
                pause_durations=pause_durations,
                filler_count_map=transcript_analysis["filler_count_map"],
                total_filler_count=transcript_analysis["total_filler_count"],
                total_words=transcript_analysis["total_words"],
                speech_speed_wpm=transcript_analysis["speech_speed_wpm"]
            )

            # Save feedback metrics to feedback.txt
            with open("feedback.txt", "w", encoding="utf-8") as f:
                f.write(f"Volume: {volume:.1f} deciBel\n")
                f.write(f"Pauses: {pauses}\n")
                f.write(f"Speech Speed: {transcript_analysis['speech_speed_wpm']:.1f} WPM\n")
                f.write(f"Filler Count: {transcript_analysis['total_filler_count']}\n")

            print("\n" + Fore.MAGENTA + "🗣️ Feedback Summary Before Optimization:\n")
            print(Fore.WHITE + "\n".join(feedback_lines[:-2]))  # Print all but wrap-up and tip

            try:
                print(Fore.CYAN + "\n🔊 Delivering feedback with Azure...\n")
                if led_connected:
                    start_processing_pattern()
                play_feedback_chime()
                speak_with_gesture("Here’s your feedback to level up your presentation!", "handsup")
                for line in feedback_lines[:-1]:  # Speak all but the last tip
                    gesture = "handsup" if "Great" in line or "Perfect" in line or "Nice" in line else "handtogether"
                    speak_with_gesture(line, gesture)
                    time.sleep(0.5)  # Short pause for clarity
                speak_with_gesture(f"Pro tip: {feedback_lines[-1]}", "handsup")  # Speak actionable tip
                if led_connected:
                    led_off()
            except Exception as e:
                print(Fore.RED + f"⚠️ TTS error: {e}")

            print(Fore.GREEN + "\n✨ Optimizing script with Gemini...\n")
            if led_connected:
                start_processing_pattern()
            optimized_script = optimize_presentation_script(transcript)

            if optimized_script.strip():
                print(Fore.CYAN + "\n📝 Optimized Script:\n")
                print(optimized_script)
                with open("optimized_output.txt", "w", encoding="utf-8") as f:
                    f.write(optimized_script)
                user_file = save_user_transcript_copy(optimized_script, transcript)
                if led_connected:
                    led_off()
                print(Fore.GREEN + "\n✅ Analysis complete! Check 'optimized_output.txt' for results.")
                if user_file:
                    print(Fore.CYAN + "💾 User session report saved for future reference!")
                else:
                    print(Fore.YELLOW + "⚠️ Main system file saved, but user backup failed.")
            else:
                print(Fore.RED + "[ERROR] Gemini returned empty script.")
        else:
            print(Fore.RED + "❌ No transcript available for analysis.")
    else:
        print(Fore.RED + "❌ Recording failed or no audio data.")
    
    print(Fore.WHITE + "\n" + "=" * 60)
    print(Fore.CYAN + "🎯 Session Complete!")