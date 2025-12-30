"""
Groq Whisper Transcription Service.
Uses Groq's ultra-fast Whisper API for transcription.
"""

import os
import logging
import tempfile
from typing import Optional
import yt_dlp
from groq import Groq
from app.models.schemas import TranscriptResponse, TranscriptSegment
logger = logging.getLogger(__name__)
class WhisperService:
    """Service for transcribing video/audio using Groq's Whisper API."""
    
    def __init__(self, model_name: str = "whisper-large-v3"):
        """
        Initialize Groq Whisper service.
        
        Args:
            model_name: Whisper model to use (whisper-large-v3 is fastest on Groq)
        """
        self.model_name = model_name
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for transcription")
        
        self.client = Groq(api_key=self.api_key)
        logger.info(f"Groq Whisper service initialized with model: {model_name}")
    
    async def transcribe_from_url_async(self, video_url: str, progress_callback=None) -> TranscriptResponse:
        """
        Async transcription for non-blocking performance.
        
        Args:
            video_url: URL to the video file
            progress_callback: Optional async function to call with progress (0-100)
            
        Returns:
            TranscriptResponse with segments and full text
        """
        import asyncio
        return await asyncio.to_thread(self.transcribe_from_url, video_url, progress_callback)
    
    def transcribe_from_url(self, video_url: str, progress_callback=None) -> TranscriptResponse:
        """
        Transcribe video from a URL using Groq's Whisper API.
        Tries to fetch existing YouTube captions first (Zero-Download).
        
        Args:
            video_url: URL to the video file
            progress_callback: Optional function to call with progress (0-100)
            
        Returns:
            TranscriptResponse with segments and full text
        """
        import time
        from youtube_transcript_api import YouTubeTranscriptApi
        from urllib.parse import urlparse, parse_qs
        
        # Ensure video_url is a string (Pydantic HttpUrl can cause issues)
        video_url = str(video_url)
        
        start_time = time.time()
        logger.info(f"Starting transcription for: {video_url}")
        
        if progress_callback:
            progress_callback(5) # Initializing

        # STRATEGY 1: Try fetching YouTube Captions (Instant)
        try:
            # Extract Video ID
            parsed_url = urlparse(video_url)
            video_id = None
            if "youtube.com" in parsed_url.netloc:
                video_id = parse_qs(parsed_url.query).get("v", [None])[0]
            elif "youtu.be" in parsed_url.netloc:
                video_id = parsed_url.path.lstrip("/")
            
            if video_id:
                logger.info(f"Detected YouTube Video ID: {video_id}. Attempting to fetch captions...")
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                
                if progress_callback:
                    progress_callback(50) # Halfway there after instant fetch

                # Convert to TranscriptResponse format
                segments = []
                full_text = []
                for item in transcript_list:
                    text = item["text"]
                    start = item["start"]
                    end = start + item["duration"]
                    segments.append(TranscriptSegment(
                        start=start,
                        end=end,
                        text=text
                    ))
                    full_text.append(text)
                
                if progress_callback:
                    progress_callback(100) # Done

                logger.info(f"✅ Fetched YouTube captions instantly! ({len(segments)} segments)")
                return TranscriptResponse(
                    segments=segments,
                    full_text=" ".join(full_text),
                    language="en"
                )
        except Exception as e:
            logger.warning(f"Could not fetch YouTube captions: {e}. Falling back to audio download.")

        # STRATEGY 2: Download Audio + Groq Whisper (Fallback)
        logger.info("Fallback: Downloading audio for Groq Whisper...")
        
        # Download audio to temp file
        download_start = time.time()
        audio_path = self._download_audio(video_url, progress_callback)
        download_time = time.time() - download_start
        logger.info(f"Audio download + conversion took: {download_time:.2f}s")
        
        if not audio_path:
            raise ValueError("Failed to download audio for transcription")
        
        try:
            # Transcribe with Groq Whisper
            logger.info("Sending to Groq Whisper API (ultra-fast)...")
            if progress_callback:
                progress_callback(90) # Almost done, waiting for API

            api_start = time.time()
            
            with open(audio_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.model_name,
                    response_format="verbose_json",
                    language="en"
                )
            
            api_time = time.time() - api_start
            total_time = time.time() - start_time
            logger.info(f"Groq API took: {api_time:.2f}s")
            logger.info(f"Total Transcription Phase took: {total_time:.2f}s")
            
            if progress_callback:
                progress_callback(100) # Done

            # Parse results
            return self._parse_result(transcription)
            
        finally:
            # Cleanup temp audio
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info("Cleaned up temp audio file")
    
    def _download_audio(self, video_url: str, progress_callback=None) -> Optional[str]:
        """
        Download audio from video URL using yt-dlp.
        Uses fast settings for speed.
        
        Args:
            video_url: URL to download from
            progress_callback: Optional function to call with progress (0-100)
            
        Returns:
            Path to downloaded audio file
        """
        # Create a unique temp file path
        output_path = os.path.join(tempfile.gettempdir(), f"groq_audio_{hash(video_url) & 0xFFFFFFFF}.mp3")
        
        def ydl_progress_hook(d):
            if d['status'] == 'downloading' and progress_callback:
                try:
                    p = d.get('_percent_str', '0%').replace('%','')
                    # Map download 0-100% to step 10-80%
                    percent = 10 + (float(p) * 0.7)
                    progress_callback(int(percent))
                except:
                    pass

        ydl_opts = {
            'format': 'worstaudio/worst',  # Fastest download (smallest file)
            'outtmpl': output_path.replace('.mp3', '.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',  # Low quality for speed (still fine for speech)
            }],
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [ydl_progress_hook],
            'concurrent_fragment_downloads': 16,
            # Turbo Download Settings (Aria2c)
            'external_downloader': 'aria2c',
            'external_downloader_args': ['-x16', '-s16', '-k1M'],
        }
        
        try:
            logger.info("Downloading audio stream (fast mode)...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Check for mp3 file
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                logger.info(f"Downloaded audio: {file_size:.1f} MB")
                return output_path
            
            # Try common extensions
            for ext in ['.webm', '.m4a', '.opus', '.mp3']:
                alt_path = output_path.replace('.mp3', ext)
                if os.path.exists(alt_path):
                    return alt_path
            
            logger.error(f"Audio file not found at: {output_path}")
            return None
            
        except Exception as e:
            logger.error(f"Audio download failed: {str(e)}")
            return None
    
    def _parse_result(self, transcription) -> TranscriptResponse:
        """
        Parse Groq transcription result into TranscriptResponse.
        
        Args:
            transcription: Groq transcription response
            
        Returns:
            Structured TranscriptResponse
        """
        segments = []
        
        # Groq returns segments in verbose_json format
        if hasattr(transcription, 'segments') and transcription.segments:
            for seg in transcription.segments:
                segments.append(TranscriptSegment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text", "").strip(),
                    speaker=None
                ))
        
        full_text = transcription.text if hasattr(transcription, 'text') else ""
        duration = segments[-1].end if segments else 0.0
        
        logger.info(f"Transcription complete: {len(segments)} segments, {duration:.1f}s duration")
        
        return TranscriptResponse(
            segments=segments,
            full_text=full_text,
            duration_seconds=duration,
            speakers_detected=1
        )
