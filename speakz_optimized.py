import azure.cognitiveservices.speech as speechsdk
import sys
import os
import time
import threading
import re
from gesture_sender import send_gesture

# ==== Azure Speech Config ====
speech_key = "1a0oyWt4KJ7CiF6OjOqZXq4cYzbkDCx8TWAqnVQJoZ4LjiKZyA0GJQQJ99BGACYeBjFXJ3w3AAAYACOGMrMv"
service_region = "eastus"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"  # Change voice if needed

# ===== GESTURE MAPPING CONFIG =====
GESTURE_TRIGGERS = {
    # Greeting and introduction gestures
    "hello": "handsup",
    "hi": "handsup", 
    "welcome": "handsup",
    "introduce": "handtogether",
    "present": "handsup",
    "today": "handsup",
    "want": "handtogether",
    
    # Emphasis and important points
    "important": "point",
    "key": "point",
    "main": "point",
    "first": "point",
    "second": "point", 
    "third": "point",
    "finally": "point",
    "remember": "point",
    "note": "point",
    
    # Descriptive gestures
    "beautiful": "handsup",
    "amazing": "handsup",
    "wonderful": "handsup",
    "great": "handsup",
    "stunning": "handsup",
    "special": "handtogether",
    "unique": "handtogether",
    "different": "handtogether",
    "blessed": "handsup",
    
    # Country/place descriptions
    "country": "handsup",
    "nation": "handsup",
    "island": "handsup",
    "land": "handsup",
    "place": "handsup",
    "sri lanka": "handsup",
    "home": "handtogether",
    
    # Nature and environment
    "waterfalls": "handsup",
    "forests": "handsup",
    "rivers": "handsup",
    "sea": "handsup",
    "ocean": "handsup",
    "mountains": "handsup",
    
    # People and relationships
    "people": "handtogether",
    "community": "handtogether",
    "family": "handtogether",
    "friends": "handtogether",
    "together": "handtogether",
    "warm": "handtogether",
    "humble": "handtogether",
    
    # Language and culture
    "speak": "point",
    "language": "point",
    "sinhala": "point",
    "culture": "handtogether",
    
    # Conclusions and endings
    "conclusion": "handtogether",
    "end": "handsdown",
    "finish": "handsdown", 
    "thank you": "handsdown",
    "goodbye": "handsdown",
}

# Gesture timing settings
GESTURE_DURATION = 2.5  # How long gestures last
SPEECH_DELAY_AFTER_GESTURE = 0.2  # Small delay for natural flow

class SynchronizedAzureSpeaker:
    def __init__(self):
        self.current_gesture = "relax"
        self.gesture_lock = threading.Lock()
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        
    def find_gesture_for_text(self, text_chunk):
        """Find the best gesture for a piece of text"""
        text_lower = text_chunk.lower()
        
        # Check for exact phrase matches first (longer phrases take priority)
        sorted_triggers = sorted(GESTURE_TRIGGERS.keys(), key=len, reverse=True)
        
        for trigger in sorted_triggers:
            if trigger in text_lower:
                print(f"🎯 Found trigger '{trigger}' -> gesture '{GESTURE_TRIGGERS[trigger]}'")
                return GESTURE_TRIGGERS[trigger]
        
        return None
    
    def split_text_with_gestures(self, full_text):
        """Split text into sentences and assign gestures"""
        # Split text into sentences
        sentences = re.split(r'[.!?]+', full_text)
        
        chunks = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Find appropriate gesture for this sentence
            gesture = self.find_gesture_for_text(sentence)
            
            chunks.append({
                'text': sentence + ".",
                'gesture': gesture
            })
        
        return chunks
    
    def perform_gesture_with_timing(self, gesture, speech_duration):
        """Perform gesture that matches speech timing"""
        def gesture_thread():
            with self.gesture_lock:
                try:
                    print(f"🤲 Starting gesture: {gesture}")
                    send_gesture(gesture)
                    self.current_gesture = gesture
                    
                    # Keep gesture active for speech duration + buffer
                    gesture_time = max(speech_duration, GESTURE_DURATION)
                    time.sleep(gesture_time)
                    
                    print(f"🤲 Ending gesture: {gesture}")
                    send_gesture("relax")
                    self.current_gesture = "relax"
                except Exception as e:
                    print(f"❌ Gesture error: {e}")
                    send_gesture("relax")
        
        thread = threading.Thread(target=gesture_thread)
        thread.daemon = True
        thread.start()
        return thread
    
    def speak_text_with_azure(self, text):
        """Speak text using Azure TTS and return duration"""
        print(f"🗣️ Azure TTS: {text[:50]}...")
        
        start_time = time.time()
        result = self.synthesizer.speak_text_async(text).get()
        end_time = time.time()
        
        speech_duration = end_time - start_time
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"✅ Speech completed in {speech_duration:.1f}s")
            return speech_duration
        else:
            print("❌ Speech synthesis failed.")
            if result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"[CANCELED] Reason: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"[ERROR] Details: {cancellation.error_details}")
            return 0
    
    def deliver_speech_with_gestures(self, text):
        """Main function to deliver speech with synchronized gestures"""
        print("🎭 Starting Azure TTS with synchronized hand gestures...")
        print("=" * 60)
        
        # Split text into gesture-mapped chunks
        chunks = self.split_text_with_gestures(text)
        print(f"📝 Speech divided into {len(chunks)} segments")
        
        # Start with neutral gesture
        send_gesture("relax")
        time.sleep(0.5)
        
        for i, chunk in enumerate(chunks):
            print(f"\n[Segment {i+1}/{len(chunks)}]")
            print(f"Text: {chunk['text']}")
            print(f"Gesture: {chunk['gesture'] or 'none'}")
            
            if chunk['gesture']:
                # Start gesture slightly before speaking
                gesture_thread = self.perform_gesture_with_timing(
                    chunk['gesture'], 
                    len(chunk['text']) * 0.1  # Rough estimate of speech time
                )
                time.sleep(SPEECH_DELAY_AFTER_GESTURE)
            
            # Speak with Azure TTS
            self.speak_text_with_azure(chunk['text'])
            
            # Small pause between segments for natural flow
            time.sleep(0.3)
        
        # Return to neutral position
        print("\n🤲 Returning to neutral position...")
        send_gesture("relax")
        time.sleep(0.5)
        
        print("=" * 60)
        print("✅ Synchronized speech delivery complete!")

def deliver_speech(text: str):
    """Enhanced version with gestures - replaces original function"""
    if not text.strip():
        print("[ERROR] No text provided to speak.")
        return
    
    try:
        speaker = SynchronizedAzureSpeaker()
        speaker.deliver_speech_with_gestures(text)
    except Exception as e:
        print(f"❌ Error during speech delivery: {e}")
        # Fallback to basic Azure TTS without gestures
        print("🔄 Falling back to basic speech without gestures...")
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("[SUCCESS] Basic speech delivered successfully.")
        else:
            print("[ERROR] Speech synthesis failed.")

# Original simple function (kept as backup)
def deliver_speech_simple(text: str):
    """Original simple speech function without gestures"""
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
            
            print("🎭 Choose delivery mode:")
            print("1. With synchronized hand gestures (default)")
            print("2. Simple speech only")
            
            try:
                # Auto-select gestures mode (you can change this)
                choice = "1"  # Default to gestures
                # Uncomment next line if you want user choice:
                # choice = input("Enter choice (1 or 2): ").strip() or "1"
                
                if choice == "2":
                    print("🗣️ Using simple speech mode...")
                    deliver_speech_simple(optimized_text)
                else:
                    print("🎭 Using synchronized gestures mode...")
                    deliver_speech(optimized_text)
                    
            except KeyboardInterrupt:
                print("\n⏹️ Speech delivery stopped by user")
                send_gesture("relax")
        else:
            print(f"[ERROR] File not found: {input_path}")
    else:
        # Or enter manually for testing
        print("Enter the optimized speech below. Press Ctrl+Z (Windows) or Ctrl+D (Linux/Mac) when done:")
        try:
            optimized_text = sys.stdin.read()
            deliver_speech(optimized_text)
        except KeyboardInterrupt:
            print("\n⏹️ Input cancelled by user")
            send_gesture("relax")