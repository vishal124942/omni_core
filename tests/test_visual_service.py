import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.visual_service import VisualIntelligenceService

async def test_visual_service():
    print("🚀 Starting VisualIntelligenceService Test...")
    service = VisualIntelligenceService()
    
    # 1. Test LinkedIn Carousel
    print("\n--- Testing LinkedIn Carousel ---")
    title = "The Future of AI Agents"
    slides = [
        "AI is no longer just a chatbot; it's an autonomous operator.",
        "The shift from 'Chat-with-PDF' to 'Build-the-App' is here.",
        "We are entering the era of Omni-Core agents that can see, hear, and do."
    ]
    
    try:
        carousel_data = await service.generate_linkedin_carousel("test_user", title, slides, style="cyberpunk")
        print(f"✅ Carousel generated successfully at: {carousel_data}")
        
        # Verify local existence (map /data to local ./data)
        local_pdf_path = carousel_data["pdf"].replace("/data", "data")
        if not os.path.exists(local_pdf_path):
            print(f"❌ ERROR: PDF file does not exist at {local_pdf_path}")
            
        for img_path in carousel_data["images"]:
            local_img_path = img_path.replace("/data", "data")
            if not os.path.exists(local_img_path):
                print(f"❌ ERROR: Slide image does not exist at {local_img_path}")
    except Exception as e:
        print(f"❌ Carousel generation failed: {str(e)}")

    # 2. Test Thumbnail Variants
    print("\n--- Testing Thumbnail Variants ---")
    transcript = "How to build an AI content agency in 2025. We will look at automation, multi-modal models, and how to scale with autonomous agents."
    
    try:
        thumbnails = await service.generate_thumbnail_variants(transcript)
        print(f"✅ {len(thumbnails)} Thumbnails generated successfully:")
        for i, path in enumerate(thumbnails):
            print(f"   [{i}] {path}")
            local_path = path.replace("/data", "data")
            if not os.path.exists(local_path):
                print(f"   ❌ ERROR: Thumbnail file does not exist at {local_path}")
    except Exception as e:
        print(f"❌ Thumbnail generation failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_visual_service())
