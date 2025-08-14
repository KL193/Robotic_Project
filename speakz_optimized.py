import azure.cognitiveservices.speech as speechsdk
import sys
import os
import time
import threading
import re
import json
from collections import defaultdict
import requests
from enhance_geature_sender import send_gesture

# ==== Azure Speech Config ====
speech_key = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
service_region = "eastus"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"

# ESP32 Configuration
ESP32_IP = "192.168.213.5"

# ===== ENHANCED GESTURE MAPPING CONFIG =====
GESTURE_TRIGGERS = {
    "hello": "handsup",
    "hi": "handsup", 
    "welcome": "handsup",
    "introduce": "handtogether",
    "present": "handsup",
    "today": "handsup",
    "want": "handtogether",
    "important": "point",
    "key": "point",
    "main": "point",
    "first": "point",
    "second": "point", 
    "third": "point",
    "finally": "point",
    "remember": "point",
    "note": "point",
    "beautiful": "handsup",
    "amazing": "handsup",
    "wonderful": "handsup",
    "great": "handsup",
    "stunning": "handsup",
    "special": "handtogether",
    "unique": "handtogether",
    "different": "handtogether",
    "blessed": "handsup",
    "country": "handsup",
    "nation": "handsup",
    "island": "handsup",
    "land": "handsup",
    "place": "handsup",
    "sri lanka": "handsup",
    "home": "handtogether",
    "waterfalls": "handsup",
    "forests": "handsup",
    "rivers": "handsup",
    "sea": "handsup",
    "ocean": "handsup",
    "mountains": "handsup",
    "people": "handtogether",
    "community": "handtogether",
    "family": "handtogether",
    "friends": "handtogether",
    "together": "handtogether",
    "warm": "handtogether",
    "humble": "handtogether",
    "speak": "point",
    "language": "point",
    "sinhala": "point",
    "culture": "handtogether",
    "conclusion": "handtogether",
    "end": "handsdown",
    "finish": "handsdown", 
    "thank you": "handsdown",
    "goodbye": "handsdown",
    "this": "point",
    "here": "point",
    "look": "point",
    "see": "point",
    "show": "point",
}

AZURE_TO_ESP32_MAPPING = {
    "handsup": "handaway",
    "handtogether": "handtogether", 
    "point": "point",
    "handsdown": "handsdown",
    "relax": "relax"
}

GESTURE_DURATION = 2.0
SPEECH_DELAY_AFTER_GESTURE = 0.1
CHUNK_DURATION = 1.5

class EnhancedSynchronizedSpeaker:
    def __init__(self):
        self.current_gesture = "relax"
        self.gesture_lock = threading.Lock()
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        self.gesture_timeline = []
        self.is_playing = False
        self.start_time = None
        
    def test_esp32_connection(self):
        try:
            response = requests.get(f"http://{ESP32_IP}/preset?action=relax", timeout=2)
            if response.status_code == 200:
                print("✅ ESP32 connection successful")
                return True
            else:
                print(f"⚠️ ESP32 responded with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ ESP32 connection failed: {e}")
            return False
    
    def send_esp32_gesture(self, azure_gesture):
        esp32_gesture = AZURE_TO_ESP32_MAPPING.get(azure_gesture, "relax")
        url = f"http://{ESP32_IP}/preset?action={esp32_gesture}"
        
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(f"🤲 ESP32 gesture '{esp32_gesture}' sent successfully")
                return True
            else:
                print(f"⚠️ ESP32 gesture failed with status {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout sending gesture '{esp32_gesture}'")
            return False
        except Exception as e:
            print(f"❌ Error sending gesture '{esp32_gesture}': {e}")
            return False
    
    def estimate_speech_duration(self, text):
        words = len(text.split())
        base_duration = words / 2.5
        punctuation_count = text.count('.') + text.count('!') + text.count('?') + text.count(',')
        pause_time = punctuation_count * 0.3
        return base_duration + pause_time
    
    def create_gesture_timeline_from_text(self, text):
        sentences = re.split(r'[.!?]+', text)
        timeline = []
        current_time = 0.0
        timeline.append({"time": 0.0, "action": "relax", "text": "[INITIAL]"})
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            gesture = self.find_gesture_for_text(sentence)
            if gesture:
                esp32_gesture = AZURE_TO_ESP32_MAPPING.get(gesture, "relax")
                timeline.append({"time": current_time, "action": esp32_gesture, "text": sentence})
            sentence_duration = self.estimate_speech_duration(sentence)
            current_time += sentence_duration + 0.5
        
        timeline.append({"time": current_time + 1.0, "action": "relax", "text": "[FINAL]"})
        return timeline
    
    def find_gesture_for_text(self, text_chunk):
        text_lower = text_chunk.lower()
        sorted_triggers = sorted(GESTURE_TRIGGERS.keys(), key=len, reverse=True)
        for trigger in sorted_triggers:
            if trigger in text_lower:
                print(f"🎯 Found trigger '{trigger}' -> gesture '{GESTURE_TRIGGERS[trigger]}'")
                return GESTURE_TRIGGERS[trigger]
        return None
    
    def gesture_sync_thread(self, timeline):
        if not timeline:
            return
        print("🎭 Starting gesture synchronization thread...")
        sent_gestures = set()
        first_gesture = timeline[0]
        self.send_esp32_gesture(first_gesture["action"])
        sent_gestures.add(first_gesture["time"])
        
        while self.is_playing:
            if not self.start_time:
                time.sleep(0.05)
                continue
            current_time = time.time() - self.start_time
            for gesture in timeline:
                if (gesture["time"] <= current_time + 0.1 and 
                    gesture["time"] not in sent_gestures):
                    print(f"⏰ {gesture['time']:.1f}s: Sending gesture '{gesture['action']}' | Text: {gesture['text'][:50]}...")
                    self.send_esp32_gesture(gesture["action"])
                    sent_gestures.add(gesture["time"])
            time.sleep(0.05)
        print("🎭 Gesture synchronization thread ended")
    
    def speak_text_with_azure_and_gestures(self, text):
        print(f"🎭 Preparing synchronized speech delivery...")
        print("=" * 60)
        self.gesture_timeline = self.create_gesture_timeline_from_text(text)
        print(f"📝 Created gesture timeline with {len(self.gesture_timeline)} gestures:")
        for i, gesture in enumerate(self.gesture_timeline):
            print(f"  {i+1:2d}. {gesture['time']:5.1f}s - {gesture['action']:12s} | {gesture.get('text', '')[:40]}")
        self.is_playing = True
        gesture_thread = threading.Thread(target=self.gesture_sync_thread, args=(self.gesture_timeline,))
        gesture_thread.daemon = True
        gesture_thread.start()
        print(f"\n🗣️ Starting Azure TTS for text: {text[:100]}...")
        self.start_time = time.time()
        result = self.synthesizer.speak_text_async(text).get()
        self.is_playing = False
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            speech_duration = time.time() - self.start_time
            print(f"✅ Speech completed in {speech_duration:.1f}s")
            time.sleep(0.5)
            self.send_esp32_gesture("relax")
            print("🤲 Final relax gesture sent")
        else:
            print("❌ Speech synthesis failed.")
            if result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"[CANCELED] Reason: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"[ERROR] Details: {cancellation.error_details}")
        print("=" * 60)
        print("✅ Enhanced synchronized speech delivery complete!")
        return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted

    def deliver_speech_with_enhanced_gestures(self, text):
        if not text.strip():
            print("❌ No text provided to speak.")
            return False
        if not self.test_esp32_connection():
            print("⚠️ ESP32 not accessible. Falling back to speech-only mode...")
            return self.deliver_speech_simple_fallback(text)
        try:
            return self.speak_text_with_azure_and_gestures(text)
        except Exception as e:
            print(f"❌ Error during enhanced speech delivery: {e}")
            return self.deliver_speech_simple_fallback(text)
    
    def deliver_speech_simple_fallback(self, text):
        print("🗣️ Using simple speech mode (no gestures)...")
        result = self.synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Simple speech delivered successfully.")
            return True
        else:
            print("❌ Speech synthesis failed.")
            return False

def deliver_speech(text: str):
    speaker = EnhancedSynchronizedSpeaker()
    return speaker.deliver_speech_with_enhanced_gestures(text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        if os.path.exists(input_path):
            with open(input_path, "r", encoding="utf-8") as f:
                optimized_text = f.read()
            print("🎭 Using enhanced synchronized gestures mode...")
            deliver_speech(optimized_text)
        else:
            print(f"[ERROR] File not found: {input_path}")
    else:
        print("Enter the optimized speech below. Press Ctrl+Z (Windows) or Ctrl+D (Linux/Mac) when done:")
        try:
            optimized_text = sys.stdin.read()
            print("🎭 Using enhanced synchronized gestures mode...")
            deliver_speech(optimized_text)
        except KeyboardInterrupt:
            print("\n⏹️ Input cancelled by user")
            try:
                requests.get(f"http://{ESP32_IP}/preset?action=relax", timeout=1)
            except:
                pass
