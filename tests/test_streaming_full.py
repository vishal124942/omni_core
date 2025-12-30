import asyncio
import httpx
import json
import time
import sys
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/process-video-stream"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=KcCFP6o56h0"
CLIENT_ID = "test_user_rigorous"
TONE_PROFILE = "controversial"

async def run_test():
    print(f"🚀 Starting Rigorous Test for: {TEST_VIDEO_URL}")
    print(f"Target Endpoint: {API_URL}")
    print("-" * 60)

    start_time = time.time()
    events_received = {
        "status": 0,
        "transcript": 0,
        "analysis": 0,
        "linkedin": 0,
        "twitter": 0,
        "blog": 0,
        "hooks": 0,
        "broll": 0,
        "seo": 0,
        "newsletter": 0,
        "airtable": 0,
        "complete": 0,
        "error": 0
    }
    
    payload = {
        "video_url": TEST_VIDEO_URL,
        "client_id": CLIENT_ID,
        "tone_profile": TONE_PROFILE
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", API_URL, json=payload) as response:
                if response.status_code != 200:
                    print(f"❌ API Error: Status {response.status_code}")
                    print(await response.aread())
                    return

                print("✅ Connection Established. Receiving Stream...")
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                        
                    try:
                        event = json.loads(line)
                        event_type = event.get("type", "unknown")
                        
                        # Track event counts
                        if event_type in events_received:
                            events_received[event_type] += 1
                        
                        # Log specific details based on type
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        if event_type == "status":
                            print(f"[{timestamp}] ℹ️  STATUS: {event.get('message')}")
                            
                        elif event_type == "transcript":
                            data = event.get("data", {})
                            text_len = len(data.get("full_text", ""))
                            print(f"[{timestamp}] 📝 TRANSCRIPT: {text_len} chars")
                            if text_len < 100:
                                print("⚠️  WARNING: Transcript seems suspiciously short!")
                                
                        elif event_type == "analysis":
                            data = event.get("data", {})
                            print(f"[{timestamp}] 🧠 ANALYSIS: Big Idea: '{data.get('big_idea')}'")
                            
                        elif event_type == "linkedin":
                            print(f"[{timestamp}] 👔 LINKEDIN: Generated ({len(event.get('data', ''))} chars)")
                            
                        elif event_type == "twitter":
                            tweets = event.get("data", [])
                            print(f"[{timestamp}] 🐦 TWITTER: {len(tweets)} tweets generated")
                            
                        elif event_type == "blog":
                            print(f"[{timestamp}] ✍️  BLOG: Generated ({len(event.get('data', ''))} chars)")
                            
                        elif event_type == "hooks":
                            hooks = event.get("data", [])
                            print(f"[{timestamp}] 🪝 HOOKS: {len(hooks)} variants generated")
                            
                        elif event_type == "broll":
                            images = event.get("data", [])
                            print(f"[{timestamp}] 🖼️  B-ROLL: {len(images)} images found")
                            
                        elif event_type == "seo":
                            score = event.get("data", {})
                            print(f"[{timestamp}] 🔍 SEO: Grade {score.get('grade')} ({score.get('score')}/{score.get('max_score')})")
                            
                        elif event_type == "newsletter":
                            print(f"[{timestamp}] 📧 NEWSLETTER: HTML Generated")
                            
                        elif event_type == "airtable":
                            print(f"[{timestamp}] 💾 AIRTABLE: Saved (Record ID: {event.get('data', {}).get('id', 'N/A')})")
                            
                        elif event_type == "complete":
                            print(f"[{timestamp}] ✅ COMPLETE: {event.get('message')}")
                            
                        elif event_type == "error":
                            print(f"[{timestamp}] ❌ ERROR: {event.get('error')}")
                            events_received["error"] += 1
                            
                    except json.JSONDecodeError:
                        print(f"❌ Failed to decode JSON: {line}")

    except Exception as e:
        print(f"❌ Test Failed with Exception: {str(e)}")
        return

    duration = time.time() - start_time
    print("-" * 60)
    print(f"🏁 Test Finished in {duration:.2f} seconds")
    print("📊 Event Summary:")
    for evt, count in events_received.items():
        mark = "✅" if count > 0 or (evt == "error" and count == 0) else "⚠️ "
        if evt == "error" and count > 0: mark = "❌"
        print(f"  {mark} {evt.ljust(12)}: {count}")

    # Final Verdict
    required_events = ["transcript", "analysis", "linkedin", "twitter", "blog", "airtable"]
    missing = [evt for evt in required_events if events_received[evt] == 0]
    
    if missing:
        print(f"\n❌ FAILED: Missing required events: {', '.join(missing)}")
        sys.exit(1)
    elif events_received["error"] > 0:
        print("\n❌ FAILED: Errors occurred during processing")
        sys.exit(1)
    else:
        print("\n✅ PASSED: All systems operational")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_test())
