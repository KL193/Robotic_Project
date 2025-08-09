import os
from google import genai
from google.genai import types
from colorama import Fore, init
from dotenv import load_dotenv

# Initialize colorama
init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

def optimize_presentation_script(transcript: str) -> str:
    if not transcript.strip():
        print(Fore.RED + "No transcript to optimize.")
        return ""

    api_key = os.getenv("GENAI_API_KEY")
    if not api_key:
        print(Fore.RED + "GENAI_API_KEY not found in .env file.")
        return ""

    # Authenticate Gemini client
    client = genai.Client(api_key=api_key)

    model = "gemini-2.5-pro"

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=transcript)],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=1.05,
        system_instruction=[
            types.Part.from_text(text="""You are a presentation script editor. The following is a raw transcript of a spoken presentation. Your task is to:
- Remove filler words (like "um", "uh", "like", "you know", "so", "basically", etc.).
- Eliminate repeated words or phrases and stammering.
- Reorganize sentences if needed for better clarity and flow.
- Optimize the script to sound natural, engaging, and suitable for a professional presentation.
- Retain the speaker's original intent and core message.
- Use clear and concise language, with a confident and inspiring tone.
Provide only one single optimized version of the script — do NOT provide multiple options or alternative versions."""),
        ],
    )

    print(Fore.GREEN + "🎯 Sending transcript to Gemini for optimization...\n")

    full_response = ""

    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                print(chunk.text, end="")
                full_response += chunk.text
    except Exception as e:
        print(Fore.RED + f"\n❌ Error while communicating with Gemini: {e}")
        return ""

    return full_response


if __name__ == "__main__":
    try:
        with open("transcript.txt", "r", encoding="utf-8") as f:
            transcript_text = f.read()
    except FileNotFoundError:
        print(Fore.RED + "Transcript file not found. Please run transcription.py first.")
        exit(1)

    optimized_text = optimize_presentation_script(transcript_text)

    if optimized_text:
        with open("optimized_transcript.txt", "w", encoding="utf-8") as out_file:
            out_file.write(optimized_text)
        print(Fore.CYAN + "\n💾 Optimized transcript saved to 'optimized_transcript.txt'")