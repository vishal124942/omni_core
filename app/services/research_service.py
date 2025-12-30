import os
import logging
import json
from typing import List, Dict, Optional

from tavily import TavilyClient
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class ResearchService:
    """
    Phase 2: Deep Research Agent (The Brain)
    Handles Fact-Checking and Trend-Jacking using Tavily API.
    """
    
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.tavily_api_key:
            logger.warning("TAVILY_API_KEY not found in environment")
            
        self.tavily = TavilyClient(api_key=self.tavily_api_key) if self.tavily_api_key else None
        self.client = AsyncOpenAI(api_key=self.openai_api_key)

    async def get_trending_context(self, topic: str) -> str:
        """
        Search for trending news related to the topic to 'jack' the trend in hooks.
        """
        if not self.tavily:
            return ""
            
        logger.info(f"Searching for trending context on: {topic}")
        
        try:
            # Search for latest news/trends
            search_query = f"trending news and current events about {topic} {os.getenv('CURRENT_DATE', '2025')}"
            search_result = self.tavily.search(query=search_query, search_depth="basic", max_results=3)
            
            # Summarize the trends using GPT-4o
            context = ""
            for res in search_result.get("results", []):
                context += f"- {res['title']}: {res['content'][:200]}...\n"
                
            summary_res = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Summarize the following search results into a short 'Trend-Jacking' context (2 sentences max). Focus on what's happening RIGHT NOW that someone would care about."},
                    {"role": "user", "content": f"TOPIC: {topic}\nSEARCH RESULTS:\n{context}"}
                ]
            )
            
            return summary_res.choices[0].message.content
        except Exception as e:
            logger.error(f"Trend-jacking search failed: {str(e)}")
            return ""

    async def fact_check_claims(self, transcript_chunk: str) -> List[Dict]:
        """
        Identify specific numeric or factual claims in the transcript and verify them.
        """
        if not self.tavily:
            return []
            
        logger.info("Extracting and fact-checking claims from transcript")
        
        try:
            # 1. Extract potential claims to verify
            extract_res = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract 2-3 specific factual or numeric claims from the following transcript that should be verified. Return as a JSON array of strings under a 'claims' key."},
                    {"role": "user", "content": f"TRANSCRIPT: {transcript_chunk[:3000]}"}
                ],
                response_format={ "type": "json_object" }
            )
            
            claims_data = json.loads(extract_res.choices[0].message.content)
            claims = claims_data.get("claims", [])
            
            if not claims:
                # Fallback if the model didn't use the 'claims' key correctly
                if isinstance(claims_data, dict) and len(claims_data) > 0:
                    claims = list(claims_data.values())[0] if isinstance(list(claims_data.values())[0], list) else []
            
            verifications = []
            
            # 2. Verify each claim in parallel
            async def verify_single_claim(claim):
                try:
                    logger.info(f"Verifying claim: {claim}")
                    search_query = f"is it true that {claim}"
                    search_result = self.tavily.search(query=search_query, search_depth="basic", max_results=2)
                    
                    context = ""
                    for res in search_result.get("results", []):
                        context += f"{res['content']}\n"
                    
                    verify_res = await self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Verify the claim based on the provided search context. Return a verdict (Correct, Misleading, or Incorrect) and a 1-sentence explanation as JSON."},
                            {"role": "user", "content": f"CLAIM: {claim}\nCONTEXT:\n{context}"}
                        ],
                        response_format={ "type": "json_object" }
                    )
                    
                    v_data = json.loads(verify_res.choices[0].message.content)
                    return {
                        "claim": claim,
                        "verdict": v_data.get("verdict", "Inconclusive"),
                        "explanation": v_data.get("explanation", "Could not verify claim.")
                    }
                except Exception as e:
                    logger.error(f"Single verification failed: {e}")
                    return None

            import asyncio
            verification_results = await asyncio.gather(*[verify_single_claim(claim) for claim in claims[:2]])
            verifications = [res for res in verification_results if res]
            
            return verifications
        except Exception as e:
            logger.error(f"Fact-checking failed: {str(e)}")
            return []
