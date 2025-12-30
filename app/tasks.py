"""
Celery tasks for background video processing.
"""

import logging
from app.celery_app import celery_app
from app.services.whisper_service import WhisperService
from app.services.airtable_service import AirtableService
from app.services.avatar_service import AvatarService
from app.chains import ContentGenerationEngine
from app.models.schemas import ContentOutput, AnalysisOutput

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="process_video")
def process_video_task(self, video_url: str, client_id: str, tone_profile: str):
    """
    Background task for processing video content.
    
    Args:
        video_url: URL to the video
        client_id: Client identifier
        tone_profile: Tone profile for content generation
        
    Returns:
        dict with processing results
    """
    import asyncio
    
    async def run_pipeline():
        try:
            # Update task state
            self.update_state(state="TRANSCRIBING", meta={"phase": 1})
            
            # Phase 1: Transcription
            logger.info(f"[CELERY] Phase 1: Transcribing video for {client_id}")
            whisper_service = WhisperService(model_name="tiny")
            transcript_response = await whisper_service.transcribe_from_url_async(video_url)
            
            if not transcript_response.full_text:
                raise ValueError("Transcription returned empty result")
            
            # Phase 2: Content Generation
            self.update_state(state="GENERATING", meta={"phase": 2})
            logger.info("[CELERY] Phase 2: Generating content...")
            content_engine = ContentGenerationEngine()
            generated_content = await content_engine.generate_all_content(
                transcript=transcript_response.full_text,
                tone_profile=tone_profile
            )
            
            # Phase 3: AI Avatar
            self.update_state(state="AVATAR", meta={"phase": 3})
            logger.info("[CELERY] Phase 3: Generating AI Avatar...")
            avatar_service = AvatarService()
            avatar_video_url = await avatar_service.generate_avatar_video(
                text=generated_content.get("linkedin_post", "")[:500]
            )
            
            # Phase 4: Store in Airtable
            self.update_state(state="STORING", meta={"phase": 4})
            logger.info("[CELERY] Phase 4: Storing in Airtable...")
            
            analysis_data = generated_content.get("analysis", {})
            analysis_output = AnalysisOutput(
                big_idea=analysis_data.get("big_idea", ""),
                strong_takes=analysis_data.get("strong_takes", [])[:3],
                tone=analysis_data.get("detected_tone", tone_profile)
            )
            
            content_output = ContentOutput(
                analysis=analysis_output,
                linkedin_post=generated_content.get("linkedin_post", ""),
                twitter_thread=generated_content.get("twitter_thread", []),
                blog_post=generated_content.get("blog_post", ""),
                avatar_video_url=avatar_video_url
            )
            
            airtable_service = AirtableService()
            record_data = airtable_service.create_record(
                client_id=client_id,
                content=content_output,
                video_url=video_url
            )
            
            logger.info(f"[CELERY] Processing complete for {client_id}")
            
            return {
                "success": True,
                "client_id": client_id,
                "airtable_url": record_data.get("url", ""),
                "content": content_output.model_dump()
            }
            
        except Exception as e:
            logger.error(f"[CELERY] Task failed: {str(e)}")
            return {
                "success": False,
                "client_id": client_id,
                "error": str(e)
            }
    
    # Run the async pipeline
    return asyncio.run(run_pipeline())
