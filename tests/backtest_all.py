"""
Comprehensive Backtest Suite for AI Content Creation Engine
Tests all core features: Transcription, Content Gen, Visuals, Audio
"""
import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

async def test_whisper_service():
    """Test Whisper transcription service."""
    print("\n🎙️ Testing WhisperService...")
    from app.services.whisper_service import WhisperService
    
    whisper = WhisperService()
    
    # Use a short public video for testing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - short and stable
    
    try:
        start = time.time()
        result = await whisper.transcribe_from_url_async(test_url)
        elapsed = time.time() - start
        
        if result.full_text and len(result.full_text) > 50:
            print(f"✅ Transcription SUCCESS ({elapsed:.1f}s)")
            print(f"   Segments: {len(result.segments)}, Duration: {result.duration_seconds:.1f}s")
            return True, result.full_text[:200]
        else:
            print(f"❌ Transcription returned empty or short result")
            return False, None
    except Exception as e:
        print(f"❌ Transcription FAILED: {str(e)}")
        return False, None


async def test_content_generation(transcript: str):
    """Test content generation engine."""
    print("\n📝 Testing ContentGenerationEngine...")
    from app.chains import ContentGenerationEngine
    
    engine = ContentGenerationEngine()
    
    try:
        start = time.time()
        results = {"analysis": None, "linkedin": None, "twitter": None, "blog": None}
        
        async for event in engine.generate_content_stream_with_tokens(
            transcript,
            tone_profile="professional",
            platforms=["linkedin", "twitter"]  # Test selective generation
        ):
            if event["type"] == "analysis":
                results["analysis"] = event["data"]
            elif event["type"] == "linkedin":
                results["linkedin"] = event["data"]
            elif event["type"] == "twitter":
                results["twitter"] = event["data"]
            elif event["type"] == "blog":
                results["blog"] = event["data"]
        
        elapsed = time.time() - start
        
        # Check results
        success = True
        if results["analysis"]:
            print(f"✅ Analysis: {results['analysis'].get('big_idea', 'N/A')[:50]}...")
        else:
            print("❌ Analysis failed")
            success = False
            
        if results["linkedin"]:
            print(f"✅ LinkedIn: {len(results['linkedin'])} chars")
        else:
            print("⚠️ LinkedIn skipped (expected if not in platforms)")
            
        if results["twitter"]:
            print(f"✅ Twitter: {len(results['twitter'])} tweets")
        else:
            print("⚠️ Twitter skipped")
        
        print(f"   Total time: {elapsed:.1f}s")
        return success, results["analysis"]
    except Exception as e:
        print(f"❌ Content generation FAILED: {str(e)}")
        return False, None


async def test_visual_service():
    """Test visual generation (carousel + thumbnails)."""
    print("\n🎨 Testing VisualIntelligenceService...")
    from app.services.visual_service import VisualIntelligenceService
    
    service = VisualIntelligenceService()
    
    # Test Carousel
    try:
        start = time.time()
        carousel = await service.generate_linkedin_carousel(
            client_id="backtest",
            title="Test Carousel",
            slides=["Slide 1 content", "Slide 2 content", "Slide 3 content"],
            style="cyberpunk"
        )
        elapsed = time.time() - start
        
        if carousel and carousel.get("pdf"):
            print(f"✅ Carousel PDF: {carousel['pdf']} ({elapsed:.1f}s)")
            print(f"   Images: {len(carousel.get('images', []))}")
        else:
            print("❌ Carousel generation returned empty")
            return False
    except Exception as e:
        print(f"❌ Carousel FAILED: {str(e)}")
        return False
    
    # Test Thumbnails
    try:
        start = time.time()
        thumbnails = await service.generate_thumbnail_variants(
            "AI content creation strategies for social media growth"
        )
        elapsed = time.time() - start
        
        if thumbnails and len(thumbnails) > 0:
            print(f"✅ Thumbnails: {len(thumbnails)} variants ({elapsed:.1f}s)")
            for t in thumbnails:
                print(f"   - {t}")
        else:
            print("❌ Thumbnail generation returned empty")
            return False
    except Exception as e:
        print(f"❌ Thumbnails FAILED: {str(e)}")
        return False
    
    return True


async def test_audio_service():
    """Test audio translation and generation."""
    print("\n🔊 Testing AudioService...")
    from app.services.audio_service import AudioService
    
    service = AudioService()
    
    # Test Translation
    try:
        translated = await service.translate_text(
            "This is a test of the neural dubbing system.",
            target_lang="ES"
        )
        if translated:
            print(f"✅ Translation (ES): {translated[:50]}...")
        else:
            print("❌ Translation returned empty")
            return False
    except Exception as e:
        print(f"❌ Translation FAILED: {str(e)}")
        return False
    
    # Test Audio Generation
    try:
        start = time.time()
        audio_path = await service.generate_cloned_audio(
            translated,
            client_id="backtest"
        )
        elapsed = time.time() - start
        
        if audio_path:
            print(f"✅ Audio generated: {audio_path} ({elapsed:.1f}s)")
            # Check if file exists locally
            local_path = audio_path.replace("/data", "data")
            if os.path.exists(local_path):
                print(f"   File size: {os.path.getsize(local_path)} bytes")
            else:
                print(f"   ⚠️ File not found locally at {local_path}")
        else:
            print("❌ Audio generation returned empty")
            return False
    except Exception as e:
        print(f"❌ Audio generation FAILED: {str(e)}")
        return False
    
    return True


async def run_all_tests():
    """Run all backtests."""
    print("=" * 60)
    print("🚀 AI CONTENT ENGINE - COMPREHENSIVE BACKTEST")
    print("=" * 60)
    
    results = {}
    
    # 1. Whisper
    success, transcript = await test_whisper_service()
    results["whisper"] = success
    
    # Skip content generation if transcription failed
    if not transcript:
        transcript = "AI is transforming content creation. Autonomous agents can now generate social media posts, blog articles, and even videos. The future of marketing is automated and personalized."
        print(f"   Using fallback transcript for subsequent tests")
    
    # 2. Content Generation
    success, analysis = await test_content_generation(transcript)
    results["content"] = success
    
    # 3. Visuals
    results["visuals"] = await test_visual_service()
    
    # 4. Audio
    results["audio"] = await test_audio_service()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 BACKTEST RESULTS")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name.upper()}")
    
    print("-" * 60)
    print(f"  TOTAL: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review logs above.")
    
    return passed == total


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
