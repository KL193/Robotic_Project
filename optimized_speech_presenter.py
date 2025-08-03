# optimized_speech_presenter.py
from config_gemini import configure_gemini
import google.generativeai as genai

def optimize_text(original_text):
    configure_gemini()

    prompt = f"""
    Please rewrite the following speech transcript creatively and professionally, remove all filler words (like 'um', 'like', 'you know'), and enhance it for a formal context:

    Original Transcript:
    \"{original_text}\"
    """

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    optimized_text = response.text.strip()

    with open("optimized_transcript.txt", "w") as f:
        f.write(optimized_text)

    return optimized_text

if __name__ == "__main__":
    with open("transcript.txt", "r") as f:
        raw_text = f.read()
    print("Original:", raw_text)
    result = optimize_text(raw_text)
    print("Optimized:", result)
