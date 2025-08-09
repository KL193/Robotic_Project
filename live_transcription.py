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
from speakz_greeting import speak_text
from led_controller import led_good, led_too_loud, led_too_soft, led_long_pause, led_off, test_connection, start_processing_pattern

init(autoreset=True)

# ===== CONFIG =====
duration = 40
sample_rate = 44100
threshold_volume = 0.01
pause_threshold_sec = 0.3

# Real-time analysis thresholds
threshold_volume_loud = 0.05  # Too loud threshold
threshold_volume_soft = 0.005  # Too soft threshold
realtime_pause_threshold = 1.0  # Long pause threshold for LED (1 second)

filler_words = {
    "um", "uh", "er", "ah", "hmm",
    "like", "you know", "i mean",
    "basically", "actually", "literally",
    "just", "so", "well", "okay",
    "right", "alright", "kind of", "sort of",
    "you see", "you get me", "you feel me",
    "anyway", "stuff like that", "things like that"
}

# Global variables for real-time analysis - FIXED: Added missing variables
led_connected = False
silence_start_time = None
audio_buffer = []
last_led_time = 0  # FIXED: Added this missing variable
led_cooldown_sec = 0.1  # FIXED: Added LED cooldown (100ms)
last_led_state = None  # Track last LED state to avoid redundant calls

def check_led_connection():
    """Test ESP32 connection at startup"""
    global led_connected
    led_connected = test_connection()
    if not led_connected:
        print(Fore.YELLOW + "[WARNING] ESP32 not connected. LEDs will not work.")
    return led_connected

def save_user_transcript_copy(optimized_text, original_transcript):
    """Save a timestamped copy of both original and optimized transcripts for user access"""
    try:
        # Create a user-friendly folder path
        user_transcripts_folder = r"D:\uoj\4 th year\Robotics\Speakz-Greetings\Robotic_Project\User_Transcripts"
        
        # Make sure the folder exists
        os.makedirs(user_transcripts_folder, exist_ok=True)
        
        # Create timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        user_filename = f"presentation_session_{timestamp}.txt"
        user_file_path = os.path.join(user_transcripts_folder, user_filename)
        
        # Create comprehensive session report
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
        
        # Save the session report
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

    # Convert to float32 if needed
    if chunk.dtype == np.int16 or chunk.dtype == np.int32:
        chunk = chunk.astype(np.float32) / 32767

    # Calculate volume
    volume = np.abs(chunk).mean()

    # Check if it's silence (potential pause)
    is_silence = volume < threshold_volume_soft

    # LED cooldown check
    now = time.time()
    if now - last_led_time < led_cooldown_sec:
        return  # Skip LED update if within cooldown

    current_led_state = None

    if is_silence:
        if silence_start_time is None:
            silence_start_time = now
        else:
            silence_duration = now - silence_start_time
            if silence_duration > realtime_pause_threshold:
                current_led_state = "long_pause"
    else:
        silence_start_time = None  # Reset silence timer

        # Check volume levels
        if volume > threshold_volume_loud:
            current_led_state = "too_loud"
        elif volume < threshold_volume_soft:
            current_led_state = "too_soft"
        else:
            current_led_state = "good"

    # Only send LED command if state changed (avoid redundant calls)
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
            
            # Debug output (optional - comment out if too verbose)
            print(f"\r[LED] Volume: {volume:.4f} -> {current_led_state}         ", end="", flush=True)
            
        except Exception as e:
            print(f"\n[LED ERROR] {e}")

def audio_callback(indata, frames, time, status):
    """Real-time audio callback for LED feedback"""
    global audio_buffer
    
    if status:
        print(f'Audio callback error: {status}')
    
    # Add to buffer for final processing
    audio_buffer.append(indata.copy())
    
    # Real-time LED analysis
    chunk = indata.flatten()
    update_led_realtime(chunk)
    
    # Print real-time feedback (less verbose version)
    volume = np.abs(chunk).mean()
    print(f"\r{Fore.CYAN}🎤 Recording... Vol: {volume:.4f}   ", end="", flush=True)

# ===== UTIL =====
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

# ===== AUDIO RECORD WITH REAL-TIME LEDs =====
def record_audio(filename="recording.wav"):
    global audio_buffer, led_connected, silence_start_time, last_led_time, last_led_state
    
    # Reset all global variables
    audio_buffer = []
    silence_start_time = None
    last_led_time = 0
    last_led_state = None
    
    # Check LED connection
    check_led_connection()
    
    print(Fore.CYAN + "🎤 Recording started with real-time LED feedback...")
    if led_connected:
        print(Fore.WHITE + "Green = Good | Red = Too loud/Long pause | Orange = Too soft")
    else:
        print(Fore.YELLOW + "LED feedback disabled (ESP32 not connected)")
    
    simulate_led("blue", "Listening...")
    
    # Record with real-time callback
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, 
                          callback=audio_callback, dtype='float32'):
            sd.sleep(int(duration * 1000))  # Convert to milliseconds
    except Exception as e:
        print(f"\n{Fore.RED}Recording error: {e}")
        return None, None
    
    # Turn off LEDs when done
    if led_connected:
        led_off()
    
    print(f"\n{Fore.CYAN}✅ Recording complete!")
    
    # Combine all audio chunks
    if audio_buffer:
        audio = np.concatenate(audio_buffer, axis=0).flatten()
        
        # Save to file
        audio_int16 = np.int16(audio * 32767)
        wav.write(filename, sample_rate, audio_int16)
        print(Fore.CYAN + "💾 Recording saved.")
        
        return filename, audio_int16.flatten()
    else:
        print(Fore.RED + "❌ No audio recorded!")
        return None, None

# ===== TRANSCRIBE =====
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
        print(Fore.RED + f"❌ Google Speech error: {e}")
        return ""

# ===== AUDIO ANALYSIS =====
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

# ===== TRANSCRIPT ANALYSIS =====
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

    if speech_speed_wpm < 100:
        simulate_led("yellow", "⚠️ Too slow")
    elif speech_speed_wpm > 160:
        simulate_led("yellow", "⚠️ Too fast")
    else:
        simulate_led("green", "✅ Speed okay")

    return {
        "filler_count_map": filler_count_map,
        "total_filler_count": total_filler_count,
        "total_words": total_words,
        "speech_speed_wpm": speech_speed_wpm
    }

# ===== FEEDBACK SUMMARY =====
def generate_feedback_summary(volume, pauses, pause_durations, filler_count_map, total_filler_count, total_words, speech_speed_wpm):
    summary = []

    if volume > 0.05:
        summary.append("Your voice was too loud at times.")
    elif volume < 0.005:
        summary.append("Your voice was too soft or almost silent.")
    else:
        summary.append("Your speaking volume was good.")

    if pauses > 3:
        summary.append(f"You had {pauses} long pauses, which could break flow.")
    elif pauses > 0:
        summary.append(f"You had {pauses} noticeable pause(s), but not excessive.")
    else:
        summary.append("You spoke fluidly without unnecessary pauses.")

    if total_filler_count > 0:
        filler_msg = f"You used {total_filler_count} filler words. "
        filler_msg += "Try to reduce them for a more polished delivery." if total_filler_count > 3 else "That's a reasonable amount."
        if filler_count_map:
            filler_msg += " You said: " + ", ".join(f"'{k}' ({v})" for k, v in filler_count_map.items()) + "."
        summary.append(filler_msg)
    else:
        summary.append("Great job! No filler words detected.")

    if speech_speed_wpm < 100:
        summary.append(f"Your speech was slow ({speech_speed_wpm:.1f} WPM).")
    elif speech_speed_wpm > 160:
        summary.append(f"Your speech was fast ({speech_speed_wpm:.1f} WPM).")
    else:
        summary.append(f"Your speech speed ({speech_speed_wpm:.1f} WPM) was ideal.")

    return " ".join(summary)

# ===== MAIN RUN =====
if __name__ == "__main__":
    print(Fore.CYAN + "🤖 Starting Speech Analysis with LED Feedback System")
    print(Fore.WHITE + "=" * 60)
    
    filename, audio = record_audio()
    
    if filename and audio is not None:
        pauses, pause_durations = analyze_audio(audio)
        transcript = transcribe_audio(filename)
        transcript_analysis = analyze_transcript(transcript, duration, pauses)

        if transcript and transcript_analysis:
            volume = np.abs(audio).mean()
            feedback = generate_feedback_summary(
                volume=volume,
                pauses=pauses,
                pause_durations=pause_durations,
                filler_count_map=transcript_analysis["filler_count_map"],
                total_filler_count=transcript_analysis["total_filler_count"],
                total_words=transcript_analysis["total_words"],
                speech_speed_wpm=transcript_analysis["speech_speed_wpm"]
            )

            print("\n" + Fore.MAGENTA + "🗣️ Feedback Summary Before Optimization:\n")
            print(Fore.WHITE + feedback)

            try:
                print(Fore.CYAN + "\n🔊 Delivering feedback with Azure...\n")
                # Yellow processing pattern while giving feedback
                if led_connected:
                    start_processing_pattern()
                speak_text(feedback)
            except Exception as e:
                print(Fore.RED + f"⚠️ TTS error: {e}")

            print(Fore.GREEN + "\n✨ Optimizing script with Gemini...\n")
            # Keep yellow processing pattern during Gemini optimization
            if led_connected:
                start_processing_pattern()
            optimized_script = optimize_presentation_script(transcript)

            if optimized_script.strip():
                print(Fore.CYAN + "\n📝 Optimized Script:\n")
                print(optimized_script)
                
                # Save the main system file (required by main_controller.py)
                with open("optimized_output.txt", "w", encoding="utf-8") as f:
                    f.write(optimized_script)
                
                # Save user copy with timestamp for future reference
                user_file = save_user_transcript_copy(optimized_script, transcript)
                
                # Turn off processing pattern when done
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