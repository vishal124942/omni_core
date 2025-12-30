"""
FastAPI application for the Omni-Channel Content Repurposing Engine.
Main orchestration endpoint for video processing pipeline.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx
import asyncio
from functools import lru_cache

from app.models.schemas import (
    VideoProcessRequest,
    ContentOutput,
    ProcessingResponse,
    AnalysisOutput,
)
from app.services.whisper_service import WhisperService
from app.services.airtable_service import AirtableService
from app.chains import ContentGenerationEngine

# Load environment variables
load_dotenv()

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# WebSocket Log Streaming - Thread-safe implementation
from collections import deque
from threading import Lock

class WebSocketLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.clients: set = set()
        self.log_queue: deque = deque(maxlen=100)  # Keep last 100 logs
        self._lock = Lock()

    def emit(self, record):
        log_entry = self.format(record)
        with self._lock:
            self.log_queue.append(log_entry)
        # Schedule async broadcast
        self._broadcast_sync(log_entry)
    
    def _broadcast_sync(self, log_entry: str):
        """Synchronously queue messages for broadcast."""
        if not self.clients:
            return
        
        # Import here to avoid circular imports
        import asyncio
        
        async def send_to_all():
            disconnected = []
            for client in list(self.clients):
                try:
                    await client.send_text(log_entry)
                except Exception:
                    disconnected.append(client)
            for client in disconnected:
                self.clients.discard(client)
        
        # Try to get running loop and schedule
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_to_all())
        except RuntimeError:
            # No running loop - skip broadcast
            pass

ws_log_handler = WebSocketLogHandler()
ws_log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.getLogger().addHandler(ws_log_handler)


# ============================================================================
# APPLICATION SETUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Omni-Channel Content Repurposing Engine...")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Omni-Channel Content Repurposing Engine",
    description="Transform video content into multi-platform marketing assets",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Note: wildcard origin requires credentials=False
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data directory exists before mounting
Path("data").mkdir(exist_ok=True)
Path("data/visuals").mkdir(exist_ok=True)
Path("data/audio").mkdir(exist_ok=True)

# Mount static files for data directory (images, PDFs, etc.)
app.mount("/data", StaticFiles(directory="data"), name="data")


# ============================================================================
# ASYNC BACKGROUND PROCESSING ENDPOINTS
# ============================================================================

@app.post("/process-video-async")
async def process_video_async(
    video_url: str,
    client_id: str = "default_client",
    tone_profile: str = "professional"
):
    """
    Start video processing in background (instant response).
    Returns task_id to poll for status.
    """
    from app.tasks import process_video_task
    
    try:
        # Queue the task
        task = process_video_task.delay(video_url, client_id, tone_profile)
        
        logger.info(f"Task queued: {task.id} for client {client_id}")
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "Processing started in background"
        }
    except Exception as e:
        logger.error(f"Failed to queue task: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to queue task: {str(e)}"
        }


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a background task.
    """
    from app.celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == "PENDING":
        return {"status": "pending", "task_id": task_id}
    elif task.state == "STARTED":
        return {"status": "started", "task_id": task_id}
    elif task.state == "SUCCESS":
        return {"status": "completed", "task_id": task_id, "result": task.result}
    elif task.state == "FAILURE":
        return {"status": "failed", "task_id": task_id, "error": str(task.result)}
    else:
        return {"status": task.state.lower(), "task_id": task_id, "meta": task.info}




@app.post("/reset-project")
async def reset_project():
    """
    Reset project data: Clear temp files from disk.
    Recursively deletes files in data/audio and data/visuals.
    """
    directories = ["data/audio", "data/visuals", "data/analysis"]
    deleted_count = 0
    
    try:
        for dir_path in directories:
            # Create if doesn't exist to avoid error
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
        
        logger.info(f"Project reset: Deleted {deleted_count} files from disk.")
        return {"success": True, "message": f"Project data reset. Files deleted: {deleted_count}"}
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        return {"success": False, "error": str(e)}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def validate_video_url(url: str) -> bool:
    """
    Validate that a video URL is accessible.
    
    Args:
        url: URL to validate
        
    Returns:
        True if accessible, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(str(url), follow_redirects=True, timeout=10.0)
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"URL validation failed for {url}: {str(e)}")
        return False


def log_error_to_file(error: Exception, context: str) -> None:
    """
    Log errors to logs.txt file.
    
    Args:
        error: The exception to log
        context: Context about where the error occurred
    """
    from datetime import datetime
    
    timestamp = datetime.now().isoformat()
    error_msg = f"[{timestamp}] Context: {context} | Error: {type(error).__name__}: {str(error)}\n"
    
    try:
        with open("logs.txt", "a") as f:
            f.write(error_msg)
    except Exception as e:
        logger.error(f"Failed to write to log file: {str(e)}")


def _check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and available."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


# ============================================================================
# PROCESSING PIPELINE
# ============================================================================

async def process_video_pipeline(
    video_url: str,
    client_id: str,
    tone_profile: str
) -> ProcessingResponse:
    """
    Main processing pipeline for video content.
    
    Args:
        video_url: URL to the video
        client_id: Client identifier
        tone_profile: Tone profile for content generation
        
    Returns:
        ProcessingResponse with results
    """
    try:
        # Phase 1: Preparation
        logger.info(f"Phase 1: Starting processing for client {client_id}")
        
        # Phase 2: Transcription (Groq Whisper - ULTRA FAST!)
        logger.info("Phase 2: Transcribing video (Groq Whisper)...")
        whisper_service = WhisperService()  # Uses Groq's whisper-large-v3
        transcript_response = await whisper_service.transcribe_from_url_async(video_url)
        
        if not transcript_response.full_text:
            raise ValueError("Transcription returned empty result")
        
        logger.info(f"Transcription complete: {len(transcript_response.segments)} segments")
        
        # Phase 3: Content Generation (No more video clipping - faster!)
        logger.info("Phase 3: Generating content...")
        content_engine = ContentGenerationEngine()
        generated_content = await content_engine.generate_all_content(
            transcript=transcript_response.full_text,
            tone_profile=tone_profile
        )
        
        logger.info("Content generation complete!")
        
        # Build analysis output
        analysis_data = generated_content.get("analysis", {})
        analysis_output = AnalysisOutput(
            big_idea=analysis_data.get("big_idea", ""),
            strong_takes=analysis_data.get("strong_takes", [])[:3],
            tone=analysis_data.get("tone", tone_profile)
        )
        
        # Phase 4: Production Features (Parallel)
        logger.info("Phase 4: Running production features in parallel...")
        
        # 4.2: Generate hook variants
        hook_variants = []
        try:
            hook_variants = await content_engine.generate_hook_variants(
                big_idea=analysis_output.big_idea,
                transcript=transcript_response.full_text[:2000],
                tone_profile=tone_profile
            )
            logger.info(f"Generated {len(hook_variants)} hook variants")
        except Exception as e:
            logger.warning(f"Hook generation failed: {str(e)}")
        
        # 4.3: Get B-Roll images
        broll_images = []
        from app.services.broll_service import BRollService
        broll_service = BRollService()
        try:
            broll_images = await broll_service.get_images_for_content(
                analysis_output.strong_takes
            )
            logger.info(f"Fetched {len(broll_images)} B-roll images")
        except Exception as e:
            logger.warning(f"B-roll fetch failed: {str(e)}")
        
        # 4.4: Score blog post SEO
        seo_score = {}
        from app.services.seo_service import SEOService
        seo_service = SEOService()
        try:
            score_result = seo_service.score_article(
                generated_content.get("blog_post", ""),
                keyword=analysis_output.big_idea.split()[0] if analysis_output.big_idea else None
            )
            seo_score = {
                "score": score_result.score,
                "max_score": score_result.max_score,
                "grade": score_result.grade,
                "feedback": score_result.feedback,
                "details": score_result.details
            }
            logger.info(f"SEO Score: {score_result.grade} ({score_result.score}/{score_result.max_score})")
        except Exception as e:
            logger.warning(f"SEO scoring failed: {str(e)}")
        
        # 4.5: Generate newsletter HTML
        newsletter_html = ""
        from app.services.newsletter_service import NewsletterService
        newsletter_service = NewsletterService()
        try:
            newsletter_html = newsletter_service.generate_html(
                big_idea=analysis_output.big_idea,
                strong_takes=analysis_output.strong_takes,
                video_url=video_url
            )
            logger.info("Newsletter HTML generated")
        except Exception as e:
            logger.warning(f"Newsletter generation failed: {str(e)}")
        
        logger.info("All production features complete!")
        
        content_output = ContentOutput(
            analysis=analysis_output,
            linkedin_post=generated_content.get("linkedin_post", ""),
            twitter_thread=generated_content.get("twitter_thread", []),
            blog_post=generated_content.get("blog_post", ""),
            linkedin_hooks=hook_variants,
            broll_images=broll_images,
            seo_score=seo_score,
            newsletter_html=newsletter_html
        )
        
        # Phase 5: Store in Airtable
        logger.info("Phase 5: Storing in Airtable...")
        airtable_service = AirtableService()
        record_data = airtable_service.create_record(
            client_id=client_id,
            content=content_output,
            video_url=video_url
        )
        
        airtable_url = record_data.get("url", "")
        
        logger.info(f"Processing complete for client {client_id}")
        
        return ProcessingResponse(
            success=True,
            message="Content generation completed successfully",
            client_id=client_id,
            airtable_record_url=airtable_url,
            content=content_output
        )
        
    except Exception as e:
        error_msg = str(e)
        log_error_to_file(e, f"process_video_pipeline for {client_id}")
        logger.error(f"Pipeline failed: {error_msg}")
        
        return ProcessingResponse(
            success=False,
            message="Processing failed",
            client_id=client_id,
            error=error_msg
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Omni-Channel Content Repurposing Engine",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "deepgram": bool(os.getenv("DEEPGRAM_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "airtable": bool(os.getenv("AIRTABLE_API_KEY")),
            "slack": bool(os.getenv("SLACK_WEBHOOK_URL")),
            "ffmpeg": _check_ffmpeg()
        }
    }


@app.post("/process-video", response_model=ProcessingResponse)
async def process_video(
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Main endpoint to process a video and generate marketing assets.
    
    Accepts a video URL and processes it through:
    1. Transcription (Deepgram)
    2. Content Generation (LangChain + GPT-4o)
    3. Video Clipping (OpusClip)
    4. Storage (Airtable)
    5. Notifications (Slack)
    
    Args:
        request: VideoProcessRequest with video_url, client_id, tone_profile
        
    Returns:
        ProcessingResponse with generated content and Airtable URL
    """
    logger.info(f"Received request for client: {request.client_id}")
    
    # Validate video URL exists
    url_valid = await validate_video_url(str(request.video_url))
    if not url_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Video URL is not accessible: {request.video_url}"
        )
    
    # Process synchronously (as per implementation plan)
    result = await process_video_pipeline(
        video_url=str(request.video_url),
        client_id=request.client_id,
        tone_profile=request.tone_profile
    )
    
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error or "Processing failed"
        )
    
    return result


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming."""
    await websocket.accept()
    ws_log_handler.clients.add(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_log_handler.clients.remove(websocket)
    except Exception:
        if websocket in ws_log_handler.clients:
            ws_log_handler.clients.remove(websocket)


# Store clip paths for serving
clip_storage: dict = {}


from fastapi.responses import FileResponse


@app.get("/clips/{clip_id}")
async def get_clip(clip_id: str):
    """
    Serve a generated video clip for download.
    
    Args:
        clip_id: The clip identifier
        
    Returns:
        The video file for download
    """
    if clip_id not in clip_storage:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    clip_path = clip_storage[clip_id]
    
    if not os.path.exists(clip_path):
        raise HTTPException(status_code=404, detail="Clip file not found on disk")
    
    return FileResponse(
        clip_path,
        media_type="video/mp4",
        filename=f"{clip_id}.mp4",
        headers={"Content-Disposition": f"attachment; filename={clip_id}.mp4"}
    )


def register_clips(clip_paths: list) -> list:
    """Register clip paths and return downloadable URLs."""
    import uuid
    logger.info(f"Registering clips. Received paths: {clip_paths}")
    urls = []
    for path in clip_paths:
        logger.info(f"Checking path: {path}, exists: {os.path.exists(path) if path else 'N/A'}")
        if path and os.path.exists(path):
            clip_id = f"clip_{uuid.uuid4().hex[:8]}"
            clip_storage[clip_id] = path
            urls.append(f"/clips/{clip_id}")
            logger.info(f"Registered clip: {clip_id} -> {path}")
    logger.info(f"Final registered URLs: {urls}")
    return urls


from fastapi.responses import StreamingResponse
import json
import asyncio

@app.post("/process-video-stream")
async def process_video_stream(request: VideoProcessRequest):
    """
    Stream the processing of a video, returning partial results as they complete.
    """
    async def event_generator():
        try:
            # Instantiate services
            whisper_service = WhisperService()
            content_engine = ContentGenerationEngine()
            airtable_service = AirtableService()
            
            # 1. Validate URL
            if not await validate_video_url(request.video_url):
                yield json.dumps({"type": "error", "error": "Invalid or inaccessible video URL"}) + "\n"
                return

            # 2. Transcribe with real-time progress
            yield json.dumps({"type": "status", "message": "Transcribing video..."}) + "\n"
            yield json.dumps({"type": "progress", "step": "transcription", "percent": 5}) + "\n"
            
            try:
                import queue
                import threading
                
                progress_queue = queue.Queue()
                last_progress = [5]  # Use list to allow mutation in nested function
                
                def progress_callback(p):
                    # Only add if progress changed significantly (avoid spam)
                    if p > last_progress[0] + 5:
                        progress_queue.put(p)
                        last_progress[0] = p
                
                # Start transcription in background
                result_container = [None, None]  # [result, error]
                
                def run_transcription():
                    try:
                        result_container[0] = whisper_service.transcribe_from_url(
                            str(request.video_url),
                            progress_callback=progress_callback
                        )
                    except Exception as e:
                        result_container[1] = e
                    finally:
                        progress_queue.put(None)  # Signal completion
                
                thread = threading.Thread(target=run_transcription)
                thread.start()
                
                # Poll for progress updates while transcription runs
                while True:
                    try:
                        progress = progress_queue.get(timeout=0.1)
                        if progress is None:
                            break  # Transcription complete
                        yield json.dumps({"type": "progress", "step": "transcription", "percent": int(progress)}) + "\n"
                    except queue.Empty:
                        await asyncio.sleep(0.05)  # Yield control to event loop
                        continue
                
                thread.join()
                
                if result_container[1]:
                    raise result_container[1]
                
                transcript_res = result_container[0]
                yield json.dumps({"type": "progress", "step": "transcription", "percent": 100}) + "\n"
                yield json.dumps({"type": "transcript", "data": transcript_res.dict()}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "error", "error": f"Transcription failed: {str(e)}"}) + "\n"
                return

            # 3. Generate Content (Streamed)
            yield json.dumps({"type": "status", "message": "Analyzing and generating content..."}) + "\n"
            yield json.dumps({"type": "progress", "step": "analysis", "percent": 50}) + "\n"
            
            # Store results for final Airtable saving
            generated_content = {
                "transcript": transcript_res.full_text,
                "analysis": None,
                "linkedin_post": None,
                "twitter_thread": [],
                "blog_post": None,
                "linkedin_hooks": [],
                "broll_images": [],
                "seo_score": None,
                "newsletter_html": None,
                "style_examples_used": []
            }
            
            async for event in content_engine.generate_content_stream_with_tokens(
                transcript_res.full_text,
                video_url=request.video_url,
                tone_profile=request.tone_profile,
                platforms=request.platforms
            ):
                # Handle thinking events (real-time token streaming)
                if event["type"] == "thinking_start":
                    yield json.dumps(event) + "\n"
                    continue
                elif event["type"] == "thinking":
                    yield json.dumps(event) + "\n"
                    continue
                elif event["type"] == "thinking_done":
                    yield json.dumps(event) + "\n"
                    continue
                
                # Update local state and track progress
                if event["type"] == "analysis":
                    generated_content["analysis"] = event["data"]
                    yield json.dumps({"type": "progress", "step": "analysis", "percent": 100}) + "\n"
                    yield json.dumps({"type": "progress", "step": "generation", "percent": 10}) + "\n"
                elif event["type"] == "linkedin":
                    generated_content["linkedin_post"] = event["data"]
                    yield json.dumps({"type": "progress", "step": "generation", "percent": 30}) + "\n"
                elif event["type"] == "twitter":
                    generated_content["twitter_thread"] = event["data"]
                    yield json.dumps({"type": "progress", "step": "generation", "percent": 50}) + "\n"
                elif event["type"] == "blog":
                    generated_content["blog_post"] = event["data"]
                    yield json.dumps({"type": "progress", "step": "generation", "percent": 75}) + "\n"
                elif event["type"] == "hooks":
                    generated_content["linkedin_hooks"] = event["data"]
                    yield json.dumps({"type": "progress", "step": "generation", "percent": 100}) + "\n"
                elif event["type"] == "progress":
                    # Forward progress events from chains.py
                    yield json.dumps(event) + "\n"
                    continue  # Don't yield the progress event again below
                
                # Yield to client
                yield json.dumps(event) + "\n"

            # 4. Run Production Features (Parallel)
            yield json.dumps({"type": "status", "message": "Generating extra assets (B-Roll, SEO, Newsletter)..."}) + "\n"
            yield json.dumps({"type": "progress", "step": "features", "percent": 10}) + "\n"
            
            async def run_broll():
                try:
                    from app.services.broll_service import BRollService
                    broll_service = BRollService()
                    if generated_content["analysis"]:
                        takes = generated_content["analysis"].get("strong_takes", [])
                        images = await broll_service.get_images_for_content(takes)
                        return {"type": "broll", "data": images}
                    return None
                except Exception as e:
                    logger.error(f"B-Roll failed: {str(e)}")
                    return None

            async def run_seo():
                try:
                    from app.services.seo_service import SEOService
                    seo_service = SEOService()
                    if generated_content["blog_post"]:
                        # score_article is synchronous
                        score = seo_service.score_article(generated_content["blog_post"])
                        # Convert SEOScore object to dict for JSON serialization
                        score_dict = {
                            "score": score.score,
                            "max_score": score.max_score,
                            "grade": score.grade,
                            "feedback": score.feedback,
                            "details": score.details
                        }
                        return {"type": "seo", "data": score_dict}
                    return None
                except Exception as e:
                    logger.error(f"SEO failed: {str(e)}")
                    return None

            async def run_newsletter():
                try:
                    from app.services.newsletter_service import NewsletterService
                    newsletter_service = NewsletterService()
                    if generated_content["analysis"]:
                        html = newsletter_service.generate_html(
                            big_idea=generated_content["analysis"].get("big_idea", ""),
                            strong_takes=generated_content["analysis"].get("strong_takes", []),
                            video_url=str(request.video_url)
                        )
                        return {"type": "newsletter", "data": html}
                    return None
                except Exception as e:
                    logger.error(f"Newsletter failed: {str(e)}")
                    return None

            # Execute features
            # Execute features
            feature_tasks = []
            
            # B-Roll is useful for almost all visual/text content
            if any(p in request.platforms for p in ["linkedin", "twitter", "blog", "visuals", "newsletter"]):
                feature_tasks.append(asyncio.create_task(run_broll()))
                
            if "blog" in request.platforms:
                feature_tasks.append(asyncio.create_task(run_seo()))
                
            if "newsletter" in request.platforms:
                feature_tasks.append(asyncio.create_task(run_newsletter()))
            
            completed_features = 0
            for completed_task in asyncio.as_completed(feature_tasks):
                res = await completed_task
                if res:
                    if res["type"] == "broll":
                        generated_content["broll_images"] = res["data"]
                    elif res["type"] == "seo":
                        generated_content["seo_score"] = res["data"]
                    elif res["type"] == "newsletter":
                        generated_content["newsletter_html"] = res["data"]
                    
                    yield json.dumps(res) + "\n"
                
                completed_features += 1
                progress = int((completed_features / len(feature_tasks)) * 100)
                yield json.dumps({"type": "progress", "step": "features", "percent": progress}) + "\n"

            # 5. Save to Airtable
            yield json.dumps({"type": "status", "message": "Saving to Airtable..."}) + "\n"
            
            # Convert dict to ContentOutput object for AirtableService
            from app.models.schemas import ContentOutput
            
            # Helper to safely get nested fields
            def safe_get(d, key, default=None):
                return d.get(key, default) if d else default

            # Ensure analysis is a dict (it might be None if analysis failed)
            analysis_data = generated_content.get("analysis") or {}
            
            # Construct AnalysisOutput object
            analysis_obj = AnalysisOutput(
                big_idea=analysis_data.get("big_idea", "N/A"),
                strong_takes=analysis_data.get("strong_takes", []),
                tone=analysis_data.get("tone", "professional")
            )

            output_obj = ContentOutput(
                analysis=analysis_obj,
                linkedin_post=generated_content["linkedin_post"] or "",
                twitter_thread=generated_content["twitter_thread"] or [],
                blog_post=generated_content["blog_post"] or "",
                linkedin_hooks=generated_content["linkedin_hooks"] or [],
                broll_images=generated_content["broll_images"] or [],
                seo_score=generated_content["seo_score"] or {},
                newsletter_html=generated_content["newsletter_html"] or "",
                style_examples_used=[]
            )
            
            # Wrap sync Airtable call to avoid blocking event loop
            airtable_res = await asyncio.to_thread(
                airtable_service.create_record,
                "default_client",
                output_obj,
                request.video_url
            )
            
            yield json.dumps({"type": "airtable", "data": airtable_res}) + "\n"
            yield json.dumps({"type": "complete", "message": "All processing complete!"}) + "\n"

        except Exception as e:
            logger.error(f"Streaming failed: {str(e)}")
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    # Headers to prevent proxy buffering (nginx, etc.)
    headers = {
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
    }
    return StreamingResponse(event_generator(), media_type="application/x-ndjson", headers=headers)


@app.post("/process-video/async")
async def process_video_async(
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Async version - starts processing in background and returns immediately.
    
    Args:
        request: VideoProcessRequest with video_url, client_id, tone_profile
        
    Returns:
        Acknowledgment with job_id
    """
    import uuid
    
    logger.info(f"Received async request for client: {request.client_id}")
    
    # Validate video URL
    url_valid = await validate_video_url(str(request.video_url))
    if not url_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Video URL is not accessible: {request.video_url}"
        )
    
    job_id = str(uuid.uuid4())
    
    # Add to background tasks
    background_tasks.add_task(
        process_video_pipeline,
        str(request.video_url),
        request.client_id,
        request.tone_profile
    )
    
    return {
        "status": "accepted",
        "job_id": job_id,
        "client_id": request.client_id,
        "message": "Processing started. You will receive a Slack notification upon completion."
    }


# ============================================================================
# RUN SERVER (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
