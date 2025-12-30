# Speakz – AI-Powered Public Speaking Robot

Speakz is an intelligent robotic system designed to assist users in improving their public speaking skills. By integrating AI-powered speech analytics, real-time feedback, and expressive robotic gestures, Speakz bridges the gap between digital intelligence and physical interaction.

# 💡 Key Features

End-to-End System Orchestration
A Python-based state machine manages the complete workflow, from speech rehearsal to AI-optimized playback.

Real-Time AI & Robotics Integration
Combines cloud-based speech intelligence and computer vision with robotic behavior for interactive feedback.

Low-Latency Network Control
REST-based HTTP communication with multiple ESP32 controllers ensures sub-100ms responsiveness.

Concurrent System Design
Multi-threaded architecture enables simultaneous vision processing, audio streaming, AI inference, networking, and actuator control.

Speech Analytics & Optimization

Words-per-minute (WPM) calculation

Filler-word detection with timestamps

AI-driven speech refinement

# 🛠️ Tech Stack

Programming & Core Logic: Python

Computer Vision: MediaPipe (face detection, landmarks, head pose estimation)

Speech AI: Azure Speech Services (Streaming STT & TTS)

Generative AI: Gemini (speech optimization and rewriting)

Embedded Communication: REST APIs, HTTP (ESP32 Web Servers)

Concurrency: Python threading / async execution

Networking & Control: requests, JSON-based command protocols

Hardware Platforms: ESP32 (multi-controller setup)

Actuators & I/O: Servo motors, LEDs, OLED displays

Data & Logging: Structured log files for transcripts, metrics, and user activity

# 🧑‍💻 My Role

As the Software Architect, I designed and implemented the host-side software system, including:

Main orchestrator for workflow management

Real-time speech processing pipeline

AI-powered speech optimization modules

Synchronization layer connecting cloud intelligence with robotic gestures and feedback

# 🤖 Hardware Integration

Thanks to my teammate Kavindu Hansana for hardware expertise and electromechanical design, which made the expressive robotic behavior possible.

# 📚 Usage

Install dependencies:

pip install -r requirements.txt


Configure ESP32 controllers: Update the IP addresses in the config file.

Run the main orchestrator:

python main.py


Start rehearsals: Speak in front of the camera and watch Speakz provide real-time feedback via LEDs and gestures.

# 📁 Project Structure
/Speakz
│
├─ /src                 # Core Python code
├─ /hardware            # ESP32 scripts & controller configs
├─ /logs                # Speech transcripts & analytics
├─ /docs                # Documentation & diagrams
└─ requirements.txt     # Python dependencies

# 🌟 Acknowledgements

Teamwork: Huge thanks to Kavindu Hansana for hardware integration

Mentors: University mentors for invaluable guidance

Libraries & Services: MediaPipe, Azure Speech Services, Gemini
