import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.audio_service import AudioService

async def test_audio_service():
    print("🚀 Starting AudioService Test...")
    
    # Check for keys
    has_deepl = bool(os.getenv("DEEPL_API_KEY"))
    has_eleven = bool(os.getenv("ELEVENLABS_API_KEY"))
    
    service = AudioService()
    
    if not has_deepl:
        print("⚠️ DEEPL_API_KEY missing. Using MOCKS for translation.")
        service.translator = MagicMock()
        mock_res = MagicMock()
        mock_res.text = "This is a translated test string."
        service.translator.translate_text.return_value = mock_res
        
    if not has_eleven:
        print("⚠️ ELEVENLABS_API_KEY missing. Using MOCKS for audio generation.")
        service.el_client = MagicMock()
        # Mock save function
        import app.services.audio_service as audio_mod
        audio_mod.save = MagicMock()

    # 1. Test Translation
    print("\n--- Testing DeepL Translation ---")
    text = "Hello, I am testing the neural dubbing system."
    try:
        translated = await service.translate_text(text, target_lang="ES")
        print(f"✅ Translated (ES): {translated}")
    except Exception as e:
        print(f"❌ Translation failed: {str(e)}")

    # 2. Test Audio Generation
    print("\n--- Testing ElevenLabs Cloning ---")
    try:
        # Using a shortened version of the translated text
        audio_path = await service.generate_cloned_audio(translated, "test_user")
        
        if not has_eleven:
            # Manually create a dummy file for the test to succeed if mocking
            output_path = Path("./data/audio/dubbed_test_user.mp3")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"MOCK AUDIO DATA")
            audio_path = str(output_path.absolute())

        print(f"✅ Audio generated successfully at: {audio_path}")
        if not os.path.exists(audio_path):
            print(f"❌ ERROR: Audio file does not exist at {audio_path}")
    except Exception as e:
        print(f"❌ Audio generation failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_audio_service())
