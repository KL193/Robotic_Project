import os
import datetime
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

    # Debug: Check if optimization worked
    print(f"\nDEBUG: Optimized text length: {len(optimized_text)}")

    if optimized_text:
        try:
            # Save to your desired folder with timestamp (as backup)
            save_path = r"C:\Users\HI\Desktop\Robotic_Project-main"
            
            # Debug: Check folder path
            print(f"DEBUG: Trying to save to: {save_path}")
            print(f"DEBUG: Folder exists: {os.path.exists(save_path)}")
            
            # Make sure the folder exists
            os.makedirs(save_path, exist_ok=True)

            # Create timestamped filename for backup
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            timestamped_filename = f"optimized_transcript_{timestamp}.txt"
            timestamped_path = os.path.join(save_path, timestamped_filename)

            # Also create the file that main_controller.py expects
            main_script_file = "optimized_output.txt"

            # Save both files
            with open(timestamped_path, "w", encoding="utf-8") as f1, \
                 open(main_script_file, "w", encoding="utf-8") as f2:
                f1.write(optimized_text)
                f2.write(optimized_text)

            print(Fore.CYAN + f"\n💾 Backup saved to: '{timestamped_path}'")
            print(Fore.CYAN + f"💾 Main script file saved as: '{main_script_file}'")
            print(Fore.GREEN + "✅ Both files saved successfully!")

        except Exception as e:
            print(Fore.RED + f"\n❌ ERROR saving files: {e}")
            print(Fore.YELLOW + "Trying to save only the main script file...")
            
            # Fallback: at least save the file main script needs
            try:
                with open("optimized_output.txt", "w", encoding="utf-8") as f:
                    f.write(optimized_text)
                print(Fore.CYAN + "💾 Main script file saved as: 'optimized_output.txt'")
            except Exception as e2:
                print(Fore.RED + f"❌ Failed to save any files: {e2}")
    else:
        print(Fore.RED + "❌ No optimized text to save. Check your API key and transcript file.")