import os
import logging
from typing import Optional, List
from pathlib import Path

import deepl
from elevenlabs.client import ElevenLabs
from elevenlabs import save

logger = logging.getLogger(__name__)

class AudioService:
    """
    Phase 3: Audio-First Upgrade (The Voice)
    Handles Translation (DeepL) and Voice Cloning (ElevenLabs).
    """
    
    OUTPUT_DIR = Path("./data/audio")
    
    def __init__(self):
        self.deepl_api_key = os.getenv("DEEPL_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        self.translator = deepl.Translator(self.deepl_api_key) if self.deepl_api_key else None
        self.el_client = ElevenLabs(api_key=self.elevenlabs_api_key) if self.elevenlabs_api_key else None
        
        # Ensure output directory exists
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def translate_text(self, text: str, target_lang: str = "ES") -> str:
        """
        Translate text using DeepL.
        Default: Spanish (ES), Hindi (HI) also supported.
        """
        if not self.translator:
            logger.warning("DeepL translator not initialized")
            return text
            
        try:
            logger.info(f"Translating text to {target_lang}")
            # target_lang for DeepL ES, HI, DE, FR etc.
            result = self.translator.translate_text(text, target_lang=target_lang)
            return result.text
        except Exception as e:
            logger.error(f"DeepL translation failed: {str(e)}")
            return text

    async def generate_cloned_audio(self, text: str, client_id: str, voice_id: Optional[str] = None) -> str:
        """
        Generate dubbed audio using ElevenLabs.
        If voice_id is provided, use that specific clone. 
        Otherwise use a high-quality default.
        """
        if not self.el_client:
            logger.warning("ElevenLabs client not initialized")
            return ""
            
        try:
            logger.info(f"Generating cloned audio for {client_id}")
            
            # Standard ElevenLabs voices available on all accounts:
            # - 21m00Tcm4TlvDq8ikWAM = Rachel (American, Female)
            # - EXAVITQu4vr4xnSDxMaL = Bella (American, Female)
            # - ErXwobaYiN019PkySvjV = Antoni (American, Male)
            # - MF3mGyEYCl7XYWbV9V6O = Elli (American, Female)
            actual_voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel
            
            # Use Flash v2.5 for sub-second low-latency generation
            audio = self.el_client.text_to_speech.convert(
                text=text,
                voice_id=actual_voice_id,
                model_id="eleven_flash_v2_5"
            )
            
            import uuid
            unique_id = uuid.uuid4().hex[:8]
            output_filename = f"dubbed_{client_id}_{unique_id}.mp3"
            output_path = self.OUTPUT_DIR / output_filename
            
            # Save the audio generator to file
            with open(output_path, "wb") as f:
                for chunk in audio:
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Dubbed audio saved to {output_path}")
            return f"/data/audio/{output_path.name}"
            
        except Exception as e:
            logger.error(f"ElevenLabs generation failed: {str(e)}")
            return ""

    def get_available_voices(self) -> List[dict]:
        """List available voices for this account."""
        if not self.el_client:
            return []
        
        try:
            voices = self.el_client.voices.get_all()
            return [{"id": v.voice_id, "name": v.name} for v in voices.voices]
        except Exception as e:
            logger.error(f"Failed to fetch voices: {str(e)}")
            return []
