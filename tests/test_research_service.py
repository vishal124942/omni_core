import asyncio
import os
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.research_service import ResearchService

async def test_research_service():
    print("🚀 Starting ResearchService Test...")
    
    # Check if we have Tavily API key
    has_keys = bool(os.getenv("TAVILY_API_KEY"))
    
    service = ResearchService()
    
    if not has_keys:
        print("⚠️ TAVILY_API_KEY missing. Using MOCKS for testing.")
        # Mock Tavily client
        service.tavily = MagicMock()
        service.tavily.search.return_value = {
            "results": [
                {"title": "OpenAI announces GPT-5", "content": "OpenAI has officially announced their next generation model, GPT-5, promising revolutionary capabilities."},
                {"title": "AI Agents taking over the workplace", "content": "A new report shows that 40% of administrative tasks are now being handled by autonomous agents."}
            ]
        }
    
    # 1. Test Trend-Jacking
    print("\n--- Testing Trend-Jacking ---")
    topic = "Autonomous AI Agents"
    try:
        trend = await service.get_trending_context(topic)
        print(f"✅ Trend Context: {trend}")
    except Exception as e:
        print(f"❌ Trend-jacking failed: {str(e)}")

    # 2. Test Fact-Checking
    print("\n--- Testing Fact-Checking ---")
    transcript = "We found that 87% of people prefer AI-generated content over human content. Also, the world is flat and the moon is made of cheese."
    
    if not has_keys:
        # Mock search results for specific claims
        def mock_search(query, **kwargs):
            if "87%" in query:
                return {"results": [{"content": "Studies show that only 20% of people prefer AI content."}]}
            return {"results": [{"content": "Scientific evidence confirms the earth is a sphere and the moon is rock."}]}
            
        service.tavily.search.side_effect = mock_search

    try:
        verifications = await service.fact_check_claims(transcript)
        print(f"✅ Fact-Checking Results:")
        for v in verifications:
            print(f"   - Claim: {v['claim']}")
            print(f"     Verdict: {v['verdict']}")
            print(f"     Explanation: {v['explanation']}")
    except Exception as e:
        print(f"❌ Fact-checking failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_research_service())
