"""
Pydantic models for request/response validation.
"""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class VideoProcessRequest(BaseModel):
    """Input payload for the /process-video endpoint."""
    
    video_url: HttpUrl = Field(..., description="URL to the video file")
    client_id: str = Field(..., min_length=1, description="Client identifier")
    tone_profile: str = Field(
        default="professional",
        description="Tone profile for content generation (e.g., educational, aggressive, empathetic)"
    )
    platforms: Optional[list[str]] = Field(
        default=None,
        description="List of platforms to generate for. If None, defaults to ALL."
    )


class TranscriptSegment(BaseModel):
    """A segment of transcribed text with timestamp and speaker info."""
    
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
    speaker: Optional[str] = Field(None, description="Speaker identifier from diarization")


class TranscriptResponse(BaseModel):
    """Complete transcript with metadata."""
    
    segments: list[TranscriptSegment] = Field(default_factory=list)
    full_text: str = Field(..., description="Complete transcript as a single string")
    duration_seconds: float = Field(..., description="Total duration of the audio")
    speakers_detected: int = Field(default=1, description="Number of speakers detected")


class AnalysisOutput(BaseModel):
    """Output from the transcript analysis chain (Task A)."""
    
    big_idea: str = Field(..., description="One sentence summary of the content")
    strong_takes: list[str] = Field(..., description="3 controversial or strong takes")
    tone: str = Field(..., description="Detected tone (e.g., educational, aggressive, empathetic)")


class ClipMetadata(BaseModel):
    """Metadata for a viral video clip."""
    
    url: str = Field(..., description="Downloadable URL to the clip")
    virality_score: int = Field(..., description="AI-generated virality score (1-100)")
    hook_type: str = Field(..., description="Type of hook detected (e.g., pattern_interrupt)")
    reason: str = Field(..., description="Brief explanation of why this is viral-worthy")


class ContentOutput(BaseModel):
    """Generated content assets from all chains."""
    
    # Analysis
    analysis: AnalysisOutput
    
    # Core Generated Content
    linkedin_post: str = Field(..., description="LinkedIn post in bro-etry format")
    twitter_thread: list[str] = Field(..., description="5-tweet thread without hashtags")
    blog_post: str = Field(..., description="1000-word SEO-optimized blog post")
    
    # Production Features
    linkedin_hooks: list[dict] = Field(default_factory=list, description="5 A/B hook variants with frameworks")
    broll_images: list[dict] = Field(default_factory=list, description="B-roll images for strong takes")
    seo_score: dict = Field(default_factory=dict, description="SEO analysis with score, grade, and feedback")
    newsletter_html: str = Field(default="", description="Ready-to-send HTML email newsletter")
    


class ProcessingResponse(BaseModel):
    """Response from the /process-video endpoint."""
    
    success: bool = Field(..., description="Whether processing completed successfully")
    message: str = Field(..., description="Status message")
    client_id: str = Field(..., description="Client identifier")
    airtable_record_url: Optional[str] = Field(None, description="URL to the Airtable record")
    content: Optional[ContentOutput] = Field(None, description="Generated content (if successful)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
