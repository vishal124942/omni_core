"""
LangChain chains and prompt templates for content generation.
Orchestrates GPT-4o via async streaming for multi-step content creation.
"""

import os
import logging
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional, Generator, AsyncGenerator
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import LLMChain, SequentialChain
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Configure logging for OpenAI errors
LOG_FILE = "logs.txt"

# Constants for consistent truncation across all endpoints
MAX_TRANSCRIPT_CHARS = 5000


def log_openai_error(error: Exception, chain_name: str) -> None:
    """Log OpenAI errors to logs.txt file."""
    timestamp = datetime.now().isoformat()
    error_msg = f"[{timestamp}] Chain: {chain_name} | Error: {type(error).__name__}: {str(error)}\n"
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(error_msg)
        logger.error(f"OpenAI error logged: {error_msg.strip()}")
    except Exception as e:
        logger.error(f"Failed to write to log file: {str(e)}")


# ============================================================================
# OUTPUT MODELS
# ============================================================================

class AnalysisResult(BaseModel):
    """Output model for transcript analysis."""
    big_idea: str = Field(description="One sentence summary capturing the core message")
    strong_takes: list[str] = Field(description="3 controversial or strong opinions from the content")
    tone: str = Field(description="The overall tone (e.g., educational, aggressive, empathetic, inspirational)")


class LinkedInPost(BaseModel):
    """Output model for LinkedIn post."""
    post: str = Field(description="The complete LinkedIn post in bro-etry format")


class TwitterThread(BaseModel):
    """Output model for Twitter thread."""
    tweets: list[str] = Field(description="List of 5 tweets forming a thread, no hashtags")


class BlogPost(BaseModel):
    """Output model for blog post."""
    title: str = Field(description="SEO-optimized blog title")
    content: str = Field(description="Full 1000-word blog post with H2 headers and bullet points")


# ============================================================================
# SYSTEM PROMPTS - Human-like, avoiding AI clichés
# ============================================================================

GHOSTWRITER_SYSTEM_PROMPT = """You are a ghostwriter for a top-tier industry thought leader. 

CRITICAL RULES:
- Write like a human speaking to a friend
- NEVER use generic AI phrases like:
  - "In the ever-evolving landscape"
  - "Delve deep"
  - "Game-changer"
  - "Leverage"
  - "Synergy"
  - "At the end of the day"
  - "It goes without saying"
- Use short, punchy sentences
- Be opinionated and specific
- Include real examples when possible
- Sound confident, not hedging

The client's tone profile is: {tone_profile}
"""

# ============================================================================
# CHAIN DEFINITIONS
# ============================================================================

def create_analysis_chain(llm: ChatOpenAI) -> LLMChain:
    """
    Task A: Analyze transcript to extract key insights.
    
    Args:
        llm: The language model to use
        
    Returns:
        LLMChain for analysis
    """
    parser = PydanticOutputParser(pydantic_object=AnalysisResult)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", GHOSTWRITER_SYSTEM_PROMPT),
        ("human", """Analyze this transcript and extract:

1. THE BIG IDEA: One sentence that captures the core message. Make it memorable and tweetable.

2. THREE STRONG TAKES: Find the 3 most controversial, bold, or counterintuitive points. These should be opinions that would make someone stop scrolling.

3. THE TONE: Identify the overall tone (educational, aggressive, empathetic, inspirational, humorous, etc.)

TRANSCRIPT:
{transcript}

{format_instructions}""")
    ])
    
    return LLMChain(
        llm=llm,
        prompt=prompt.partial(format_instructions=parser.get_format_instructions()),
        output_key="analysis",
        verbose=True
    )


def create_linkedin_chain(llm: ChatOpenAI) -> LLMChain:
    """
    Task B: Create LinkedIn post from analysis.
    
    Args:
        llm: The language model to use
        
    Returns:
        LLMChain for LinkedIn post generation
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", GHOSTWRITER_SYSTEM_PROMPT),
        ("human", """Write a LinkedIn post based on this analysis.

ANALYSIS:
Big Idea: {big_idea}
Strong Takes: {strong_takes}
Tone: {detected_tone}

REQUIREMENTS - "BRO-ETRY" FORMAT:
- Hook in the FIRST LINE (pattern interrupt, bold claim, or question)
- Short lines (5-10 words max per line)
- Lots of white space between thoughts
- Maximum 750 characters
- CTA in the last line (ask a question, invite comments)
- NO hashtags in the post
- NO emojis (or maximum 1-2)

Write a post that would make someone stop scrolling and engage.

Output ONLY the post text, nothing else.""")
    ])
    
    return LLMChain(
        llm=llm,
        prompt=prompt,
        output_key="linkedin_post",
        verbose=True
    )


def create_twitter_chain(llm: ChatOpenAI) -> LLMChain:
    """
    Task C: Create Twitter thread from analysis.
    
    Args:
        llm: The language model to use
        
    Returns:
        LLMChain for Twitter thread generation
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", GHOSTWRITER_SYSTEM_PROMPT),
        ("human", """Write a 5-tweet thread based on this analysis.

ANALYSIS:
Big Idea: {big_idea}
Strong Takes: {strong_takes}
Tone: {detected_tone}

REQUIREMENTS:
- Tweet 1: A HOOK that makes people want to read more. Start with a bold claim, surprising stat, or pattern interrupt.
- Tweets 2-4: Expand on the strong takes. One main point per tweet.
- Tweet 5: Conclusion with a takeaway or CTA

CONSTRAINTS:
- NO hashtags anywhere
- Each tweet must be under 280 characters
- Make each tweet standalone valuable (people might only see one)
- Use line breaks within tweets for readability

Output format - provide exactly 5 tweets, each on a new line, separated by "---":

Tweet 1
---
Tweet 2
---
Tweet 3
---
Tweet 4
---
Tweet 5""")
    ])
    
    return LLMChain(
        llm=llm,
        prompt=prompt,
        output_key="twitter_thread_raw",
        verbose=True
    )


def create_blog_chain(llm: ChatOpenAI) -> LLMChain:
    """
    Task D: Create SEO-optimized blog post from analysis.
    
    Args:
        llm: The language model to use
        
    Returns:
        LLMChain for blog post generation
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", GHOSTWRITER_SYSTEM_PROMPT),
        ("human", """Write a 1,000-word SEO-optimized blog post based on this content.

ANALYSIS:
Big Idea: {big_idea}
Strong Takes: {strong_takes}
Tone: {detected_tone}

ORIGINAL TRANSCRIPT (for context and quotes):
{transcript}

REQUIREMENTS:
- Compelling H1 title (SEO-friendly, includes main keyword naturally)
- 4-6 H2 subheadings throughout
- Bullet points for lists and key takeaways
- Short paragraphs (2-3 sentences max)
- Include quotes from the transcript where appropriate
- Professional but conversational tone
- Clear intro, body, and conclusion
- End with a strong CTA or thought-provoking question
- Target: approximately 1,000 words

FORMAT:
# [Title]

[Intro paragraph]

## [First H2]
[Content with bullet points where appropriate]

...continue with more H2 sections...

## Conclusion
[Wrap-up with CTA]

Output the complete blog post in markdown format.""")
    ])
    
    return LLMChain(
        llm=llm,
        prompt=prompt,
        output_key="blog_post",
        verbose=True
    )


# ============================================================================
# CONTENT GENERATION ENGINE
# ============================================================================

class ContentGenerationEngine:
    """
    Main engine for generating content from transcripts.
    Orchestrates multiple LangChain chains with parallel execution.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o",
        fast_model: str = "gpt-4o-mini",
        temperature: float = 0.7
    ):
        """
        Initialize the content generation engine with multiple model tiers.
        
        Args:
            openai_api_key: OpenAI API key. If not provided, reads from env.
            model: Main model for high-quality generation (default: gpt-4o)
            fast_model: Faster model for analysis and lighter tasks (default: gpt-4o-mini)
            temperature: Temperature for generation (default: 0.7)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        # Fast model for analysis (lower latency)
        self.fast_llm = ChatOpenAI(
            model=fast_model,
            temperature=0.3,  # Lower temp for analysis
            api_key=self.api_key
        )
        
        # High-quality model for content generation
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=self.api_key
        )
        
        # Initialize chains with appropriate models
        self.analysis_chain = create_analysis_chain(self.fast_llm)  # Fast analysis
        self.linkedin_chain = create_linkedin_chain(self.fast_llm)  # Fast content
        self.twitter_chain = create_twitter_chain(self.fast_llm)    # Fast content
        self.blog_chain = create_blog_chain(self.llm)               # High quality content
    
    async def generate_all_content(
        self,
        transcript: str,
        tone_profile: str = "professional"
    ) -> dict:
        """
        Generate all content types from a transcript in parallel.
        
        Args:
            transcript: The full transcript text
            tone_profile: Tone to match in generation
            
        Returns:
            Dictionary with all generated content
        """
        results = {
            "analysis": None,
            "linkedin_post": None,
            "twitter_thread": [],
            "blog_post": None,
            "errors": []
        }
        
        # Step 1: Analyze transcript (Sequential because others depend on it)
        try:
            logger.info("Running analysis chain...")
            analysis_result = await self.analysis_chain.ainvoke({
                "transcript": transcript,
                "tone_profile": tone_profile
            })
            
            # Parse the analysis output
            analysis_text = analysis_result.get("analysis", "")
            parsed_analysis = self._parse_analysis(analysis_text)
            results["analysis"] = parsed_analysis
            
        except Exception as e:
            log_openai_error(e, "analysis_chain")
            results["errors"].append(f"Analysis failed: {str(e)}")
            # Use defaults for downstream chains
            parsed_analysis = {
                "big_idea": "Key insights from the video",
                "strong_takes": ["Point 1", "Point 2", "Point 3"],
                "detected_tone": tone_profile
            }
            results["analysis"] = parsed_analysis
        
        # Step 2: Generate LinkedIn, Twitter, and Blog in parallel
        logger.info("Running downstream chains in parallel...")
        
        async def run_linkedin():
            try:
                res = await self.linkedin_chain.ainvoke({
                    "big_idea": parsed_analysis.get("big_idea", ""),
                    "strong_takes": str(parsed_analysis.get("strong_takes", [])),
                    "detected_tone": parsed_analysis.get("detected_tone", tone_profile),
                    "tone_profile": tone_profile
                })
                results["linkedin_post"] = res.get("linkedin_post", "")
            except Exception as e:
                log_openai_error(e, "linkedin_chain")
                results["errors"].append(f"LinkedIn generation failed: {str(e)}")

        async def run_twitter():
            try:
                res = await self.twitter_chain.ainvoke({
                    "big_idea": parsed_analysis.get("big_idea", ""),
                    "strong_takes": str(parsed_analysis.get("strong_takes", [])),
                    "detected_tone": parsed_analysis.get("detected_tone", tone_profile),
                    "tone_profile": tone_profile
                })
                raw_thread = res.get("twitter_thread_raw", "")
                results["twitter_thread"] = self._parse_twitter_thread(raw_thread)
            except Exception as e:
                log_openai_error(e, "twitter_chain")
                results["errors"].append(f"Twitter generation failed: {str(e)}")

        async def run_blog():
            try:
                res = await self.blog_chain.ainvoke({
                    "big_idea": parsed_analysis.get("big_idea", ""),
                    "strong_takes": str(parsed_analysis.get("strong_takes", [])),
                    "detected_tone": parsed_analysis.get("detected_tone", tone_profile),
                    "transcript": transcript[:5000],  # Limit transcript size
                    "tone_profile": tone_profile
                })
                results["blog_post"] = res.get("blog_post", "")
            except Exception as e:
                log_openai_error(e, "blog_chain")
                results["errors"].append(f"Blog generation failed: {str(e)}")

        # Execute all three concurrently
        await asyncio.gather(run_linkedin(), run_twitter(), run_blog())
        
        return results

    async def generate_content_stream(
        self,
        transcript: str,
        tone_profile: str = "professional"
    ):
        """
        Generate content in a stream, yielding results as they complete.
        Yields:
            dict: {"type": "event_type", "data": ...}
        """
        # Step 1: Analyze transcript (Sequential)
        logger.info("Running analysis chain...")
        analysis_res = await self.analysis_chain.ainvoke({
            "transcript": transcript,
            "tone_profile": tone_profile
        })
        
        # Parse analysis
        try:
            # LLMChain returns a dict with the output_key
            content = analysis_res.get("analysis", "")
            if not content:
                raise ValueError("Analysis result is empty")
                
            # Clean up markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            analysis_data = json.loads(content.strip())
            yield {"type": "analysis", "data": analysis_data}
            
            # Extract data for next steps
            big_idea = analysis_data.get("big_idea", "")
            strong_takes = analysis_data.get("strong_takes", [])
            detected_tone = analysis_data.get("tone", "professional")
            
        except Exception as e:
            logger.error(f"Analysis parsing failed: {str(e)}")
            yield {"type": "error", "error": f"Analysis failed: {str(e)}"}
            return

        # Step 2: Run downstream chains in parallel
        logger.info("Running downstream chains in parallel...")
        
        # Define tasks
        async def run_linkedin():
            try:
                res = await self.linkedin_chain.ainvoke({
                    "big_idea": big_idea,
                    "strong_takes": strong_takes,
                    "tone_profile": tone_profile,
                    "detected_tone": detected_tone
                })
                return {"type": "linkedin", "data": res.get("linkedin_post", "")}
            except Exception as e:
                return {"type": "error", "error": f"LinkedIn failed: {str(e)}"}

        async def run_twitter():
            try:
                res = await self.twitter_chain.ainvoke({
                    "big_idea": big_idea,
                    "strong_takes": strong_takes,
                    "tone_profile": tone_profile,
                    "detected_tone": detected_tone
                })
                tweets = self._parse_twitter_thread(res.get("twitter_thread_raw", ""))
                return {"type": "twitter", "data": tweets}
            except Exception as e:
                return {"type": "error", "error": f"Twitter failed: {str(e)}"}

        async def run_blog():
            try:
                res = await self.blog_chain.ainvoke({
                    "big_idea": big_idea,
                    "strong_takes": strong_takes,
                    "transcript": transcript,
                    "tone_profile": tone_profile,
                    "detected_tone": detected_tone
                })
                return {"type": "blog", "data": res.get("blog_post", "")}
            except Exception as e:
                return {"type": "error", "error": f"Blog failed: {str(e)}"}

        async def run_hooks():
            try:
                hooks = await self.generate_hook_variants(big_idea, transcript, tone_profile)
                return {"type": "hooks", "data": hooks}
            except Exception as e:
                return {"type": "error", "error": f"Hooks failed: {str(e)}"}

        # Execute all tasks and yield as they complete
        tasks = [
            asyncio.create_task(run_linkedin()),
            asyncio.create_task(run_twitter()),
            asyncio.create_task(run_blog()),
            asyncio.create_task(run_hooks())
        ]
        
        completed_count = 0
        total_tasks = len(tasks)
        
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            yield result
            
            # Yield progress for the generation step
            completed_count += 1
            progress = int((completed_count / total_tasks) * 100)
            yield {"type": "progress", "step": "generation", "percent": progress}

    async def generate_content_stream_with_tokens(
        self,
        transcript: str,
        video_url: str,
        tone_profile: str = "professional",
        platforms: list[str] = None
    ):
        """
        Generate content with real-time token streaming (like ChatGPT).
        Yields individual tokens as they're generated.
        
        Args:
            transcript: Video transcript
            tone_profile: Tone for content
            platforms: List of platforms to generate for (default: all)
        
        Yields:
            dict: {"type": "thinking", "step": "...", "token": "..."} for each token
            dict: {"type": "thinking_done", "step": "...", "content": "..."} when complete
        """
        if platforms is None:
            logger.info("Platforms list is None, defaulting to ALL platforms.")
            platforms = ["twitter", "linkedin", "blog", "newsletter", "audio", "visuals"]
        else:
            logger.info(f"Received platforms list: {platforms}")
        
        from langchain_openai import ChatOpenAI
        
        # Create streaming LLM
        streaming_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=self.api_key,
            streaming=True
        )
        
        # Step 1: Analysis with streaming
        yield {"type": "thinking_start", "step": "analysis", "label": "Analyzing transcript..."}
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", GHOSTWRITER_SYSTEM_PROMPT),
            ("human", """Analyze this transcript and extract:

1. THE BIG IDEA: One sentence that captures the core message. Make it memorable and tweetable.

2. THREE STRONG TAKES: Find the 3 most controversial, bold, or counterintuitive points. These should be opinions that would make someone stop scrolling.

3. THE TONE: Identify the overall tone (educational, aggressive, empathetic, inspirational, humorous, etc.)

TRANSCRIPT:
{transcript}

Return as JSON: {{"big_idea": "...", "strong_takes": ["...", "...", "..."], "tone": "..."}}""")
        ])
        
        analysis_content = ""
        async for chunk in streaming_llm.astream(
            analysis_prompt.format_messages(transcript=transcript[:5000], tone_profile=tone_profile)
        ):
            if hasattr(chunk, 'content') and chunk.content:
                analysis_content += chunk.content
                yield {"type": "thinking", "step": "analysis", "token": chunk.content}
        
        # Parse analysis
        try:
            if "```json" in analysis_content:
                analysis_content = analysis_content.split("```json")[1].split("```")[0]
            elif "```" in analysis_content:
                analysis_content = analysis_content.split("```")[1].split("```")[0]
            analysis_data = json.loads(analysis_content.strip())
        except:
            analysis_data = {"big_idea": "Key insights", "strong_takes": [], "tone": "professional"}
        
        yield {"type": "thinking_done", "step": "analysis", "content": analysis_data}
        yield {"type": "analysis", "data": analysis_data}
        
        big_idea = analysis_data.get("big_idea", "")
        strong_takes = analysis_data.get("strong_takes", [])
        detected_tone = analysis_data.get("tone", "professional")
        
        # Step 1.5: Deep Research (Phase 2)
        yield {"type": "thinking_start", "step": "research", "label": "Performing deep research & fact-checking..."}
        
        from app.services.research_service import ResearchService
        research_service = ResearchService()
        
        # Run research in parallel
        trend_task = asyncio.create_task(research_service.get_trending_context(big_idea))
        facts_task = asyncio.create_task(research_service.fact_check_claims(transcript[:3000]))
        
        # We don't stream tokens for research as it's API-based, but we yield a status
        trend_context, fact_checks = await asyncio.gather(trend_task, facts_task)
        
        research_data = {
            "trend_context": trend_context,
            "fact_checks": fact_checks
        }
        
        yield {"type": "thinking_done", "step": "research", "content": research_data}
        yield {"type": "research", "data": research_data}
        
        # Enriched prompt context
        research_context = f"\nTRENDING CONTEXT: {trend_context}\n" if trend_context else ""
        if fact_checks:
            research_context += "FACT CHECKS:\n"
            for f in fact_checks:
                research_context += f"- {f['claim']}: {f['verdict']} ({f['explanation']})\n"
        
        # Step 2: LinkedIn with streaming (if selected)
        # --- PARALLEL GENERATION STARTS HERE ---
        # We launch long-running tasks (Twitter, Blog, Visuals) in the background
        # while taking the user through the LinkedIn creation process (Foreground Stream).
        
        background_tasks = []

        # 1. Define Background Tasks
        
        # Twitter Task
        async def generate_twitter_task():
            if "twitter" not in platforms: return None
            try:
                # Use a fresh LLM instance for parallel execution to avoid state issues
                twitter_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=self.api_key)
                
                twitter_prompt = ChatPromptTemplate.from_messages([
                    ("system", GHOSTWRITER_SYSTEM_PROMPT),
                    ("human", """Based on the analysis, write a viral Twitter thread (6-10 tweets).
    
    ANALYSIS:
    Big Idea: {big_idea}
    Strong Takes: {strong_takes}
    Tone: {detected_tone}
    
    REQUIREMENTS:
    - Hook tweet (no hashtags, just pure value/intrigue)
    - 4-8 body tweets expanding on the strong takes
    - 1 summary tweet
    - 1 CTA tweet
    - Use the tone profile: {tone_profile}
    
    Output format:
    Tweet 1
    ---
    Tweet 2
    ---
    Tweet 3
    ...
    """)
                ])
                
                # yield {"type": "thinking_start", "step": "twitter", "label": "Drafting Twitter thread (Background)..."}
                res = await twitter_llm.ainvoke(twitter_prompt.format_messages(
                    big_idea=big_idea,
                    strong_takes=str(strong_takes),
                    detected_tone=detected_tone,
                    tone_profile=tone_profile
                ))
                tweets = self._parse_twitter_thread(res.content)
                return {"type": "twitter", "data": tweets}
            except Exception as e:
                logger.error(f"Twitter generation failed: {e}")
                return None

        # Blog Task
        async def generate_blog_task():
            if "blog" not in platforms: return None
            try:
                blog_llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=self.api_key)
                blog_prompt = ChatPromptTemplate.from_messages([
                    ("system", GHOSTWRITER_SYSTEM_PROMPT),
                    ("human", """Write a 1,000-word SEO-optimized blog post.
    
    ANALYSIS:
    Big Idea: {big_idea}
    Strong Takes: {strong_takes}
    Tone: {detected_tone}
    
    REQUIREMENTS:
    - Compelling H1 title (SEO-friendly)
    - 4-6 H2 subheadings throughout
    - Bullet points for lists and key takeaways
    - Short paragraphs (2-3 sentences max)
    - Professional but conversational tone
    - End with a strong CTA
    
    Output the complete blog post in markdown format.""")
                ])
                
                res = await blog_llm.ainvoke(blog_prompt.format_messages(
                    big_idea=big_idea,
                    strong_takes=str(strong_takes),
                    detected_tone=detected_tone,
                    transcript=transcript[:3000],
                    tone_profile=tone_profile
                ))
                return {"type": "blog", "data": res.content}
            except Exception as e:
                logger.error(f"Blog generation failed: {e}")
                return None

        # Newsletter Task
        async def generate_newsletter_task():
            if "newsletter" not in platforms: return None
            try:
                from app.services.newsletter_service import NewsletterService
                newsletter_service = NewsletterService()
                newsletter_html = await asyncio.to_thread(
                    newsletter_service.generate_html,
                    big_idea=big_idea,
                    strong_takes=strong_takes,
                    video_url=video_url
                )
                return {"type": "newsletter", "data": newsletter_html}
            except Exception as e:
                logger.error(f"Newsletter generation failed: {e}")
                return None

        # Visuals Task (Carousel + Thumbnails)
        async def generate_visuals_task():
            if "visuals" not in platforms: return None
            try:
                from app.services.visual_service import VisualIntelligenceService
                visual_service = VisualIntelligenceService()
                
                # Run Carousel and Thumbnails in parallel inner tasks
                styles = ["cyberpunk", "minimalist", "corporate"]
                
                carousel_future = visual_service.batch_generate_carousels(
                    client_id="demo_user",
                    title=big_idea[:50],
                    slides=strong_takes,
                    styles=styles
                )
                
                thumb_future = visual_service.generate_thumbnail_variants(big_idea)
                
                carousel_variants, thumbnails = await asyncio.gather(carousel_future, thumb_future)
                
                return [
                    {"type": "carousel", "data": {"variants": carousel_variants, "default_style": "cyberpunk"}},
                    {"type": "thumbnails", "data": thumbnails}
                ]
            except Exception as e:
                logger.error(f"Visuals generation failed: {e}")
                return None

        # Hooks Task
        async def generate_hooks_task():
            if "linkedin" not in platforms: return None
            try:
                hooks = await self.generate_hook_variants(big_idea, transcript, tone_profile)
                return {"type": "hooks", "data": hooks}
            except Exception as e:
                logger.error(f"Hooks generation failed: {e}")
                return None

        # 2. Launch Background Tasks
        if "twitter" in platforms: background_tasks.append(asyncio.create_task(generate_twitter_task()))
        if "blog" in platforms: background_tasks.append(asyncio.create_task(generate_blog_task()))
        if "newsletter" in platforms: background_tasks.append(asyncio.create_task(generate_newsletter_task()))
        if "visuals" in platforms: background_tasks.append(asyncio.create_task(generate_visuals_task()))
        if "linkedin" in platforms: background_tasks.append(asyncio.create_task(generate_hooks_task()))

        # 3. Execute Foreground Task (LinkedIn Post Stream)
        linkedin_content = ""
        if "linkedin" in platforms:
            yield {"type": "thinking_start", "step": "linkedin", "label": "Writing LinkedIn post (Allocating parallel workers for other tasks)..."}
            
            linkedin_prompt = ChatPromptTemplate.from_messages([
                ("system", GHOSTWRITER_SYSTEM_PROMPT),
                ("human", f"""Write a LinkedIn post based on this analysis and research.
    {research_context}
    ANALYSIS:
    Big Idea: {big_idea}
    Strong Takes: {strong_takes}
    Tone: {detected_tone}
    
    REQUIREMENTS - "BRO-ETRY" FORMAT:
    - Hook in the FIRST LINE (pattern interrupt, bold claim, or question)
    - Short lines (5-10 words max per line)
    - Lots of white space between thoughts
    - Maximum 750 characters
    - CTA in the last line (ask a question, invite comments)
    - NO hashtags in the post
    - NO emojis (or maximum 1-2)
    
    Write a post that would make someone stop scrolling and engage.
    
    Output ONLY the post text, nothing else.""")
            ])
            
            async for chunk in streaming_llm.astream(
                linkedin_prompt.format_messages(
                    big_idea=big_idea,
                    strong_takes=str(strong_takes),
                    detected_tone=detected_tone,
                    tone_profile=tone_profile
                )
            ):
                if hasattr(chunk, 'content') and chunk.content:
                    linkedin_content += chunk.content
                    yield {"type": "thinking", "step": "linkedin", "token": chunk.content}
            
            yield {"type": "thinking_done", "step": "linkedin", "content": linkedin_content}
            yield {"type": "linkedin", "data": linkedin_content}

        # 4. Execute Dependent Task (Audio) - Needs LinkedIn Content
        if "audio" in platforms:
            yield {"type": "thinking_start", "step": "audio", "label": "Cloning voice & translating audio (Waiting for post)..."}
            try:
                from app.services.audio_service import AudioService
                audio_service = AudioService()
                
                dub_text = linkedin_content[:300] if linkedin_content else "No content available for dubbing."
                translated_text = await audio_service.translate_text(dub_text, target_lang="ES")
                audio_path = await audio_service.generate_cloned_audio(translated_text, client_id="demo_user")
                
                yield {"type": "thinking_done", "step": "audio", "content": {"path": audio_path, "lang": "Spanish"}}
                yield {"type": "audio", "data": {"path": audio_path, "lang": "Spanish"}}
            except Exception as e:
                logger.error(f"Audio generation failed: {e}")
                yield {"type": "thinking_done", "step": "audio", "content": {"error": str(e)}}

        # 5. Gather and Yield Background Results
        if background_tasks:
            # yield {"type": "thinking_start", "step": "generation", "label": "Finalizing parallel tasks..."}
            results = await asyncio.gather(*background_tasks, return_exceptions=True)
            
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Background task execution failed: {res}")
                    continue
                if not res:
                    continue
                    
                # Handle list of results (from Visuals task which returns [Carousel, Thumbnails])
                if isinstance(res, list):
                    for item in res:
                        if item: yield item
                else:
                    yield res
    
    def _parse_analysis(self, analysis_text: str) -> dict:
        """
        Parse analysis output into structured format.
        
        Args:
            analysis_text: Raw analysis output text
            
        Returns:
            Parsed analysis dictionary
        """
        import json
        
        try:
            # Try to parse as JSON first
            if "{" in analysis_text:
                json_start = analysis_text.find("{")
                json_end = analysis_text.rfind("}") + 1
                json_str = analysis_text[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        result = {
            "big_idea": "",
            "strong_takes": [],
            "tone": "professional"
        }
        
        lines = analysis_text.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            lower_line = line.lower()
            if "big idea" in lower_line or "core message" in lower_line:
                current_section = "big_idea"
            elif "strong" in lower_line and "take" in lower_line:
                current_section = "strong_takes"
            elif "tone" in lower_line:
                current_section = "tone"
            elif current_section == "big_idea" and result["big_idea"] == "":
                result["big_idea"] = line.strip("- ").strip()
            elif current_section == "strong_takes" and line.startswith(("-", "•", "1", "2", "3")):
                take = line.lstrip("-•123. ").strip()
                if take:
                    result["strong_takes"].append(take)
            elif current_section == "tone" and result["tone"] == "professional":
                result["tone"] = line.strip("- ").strip()
        
        return result
    
    def _parse_twitter_thread(self, raw_thread: str) -> list[str]:
        """
        Parse raw Twitter thread output into list of tweets.
        
        Args:
            raw_thread: Raw thread output with separators
            
        Returns:
            List of tweet strings
        """
        # Split by separator
        tweets = raw_thread.split("---")
        
        # Clean up each tweet
        cleaned_tweets = []
        for tweet in tweets:
            tweet = tweet.strip()
            # Remove "Tweet X:" prefix if present
            if tweet.lower().startswith("tweet"):
                lines = tweet.split("\n", 1)
                if len(lines) > 1:
                    tweet = lines[1].strip()
                elif ":" in lines[0]:
                    tweet = lines[0].split(":", 1)[1].strip()
            
            if tweet:
                cleaned_tweets.append(tweet)
        
        return cleaned_tweets[:5]  # Ensure max 5 tweets
    
    async def generate_hook_variants(
        self,
        big_idea: str,
        transcript: str,
        tone_profile: str = "professional"
    ) -> list[dict]:
        """
        Generate 5 different hook variants using psychological frameworks.
        
        Args:
            big_idea: The main idea from the video
            transcript: Original transcript for context
            tone_profile: Tone to match
            
        Returns:
            List of hook variant dictionaries
        """
        HOOK_FRAMEWORKS = {
            "contrarian": "Start with 'Why everyone is wrong about...' or 'The uncomfortable truth about...' - challenge conventional wisdom",
            "story": "Start with a personal micro-story: 'I lost $X yesterday...' or 'Last week, I almost...' - make it emotional and specific",
            "listicle": "Start with a numbered promise: '5 ways to...' or '3 mistakes that...' - promise specific value",
            "question": "Start with a provocative question that makes them stop scrolling and think. No easy yes/no questions.",
            "stat": "Start with a shocking statistic: 'Only 3% of people know this...' or '87% of leaders fail at...' - use numbers"
        }
        
        hooks = []
        
        async def generate_single_hook(framework: str, instruction: str):
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are writing hooks for LinkedIn posts. 
Tone: {tone_profile}
NEVER use AI clichés. Sound human and punchy."""),
                ("human", f"""Write ONE opening hook for a LinkedIn post about: {big_idea}

Framework: {framework}
Instruction: {instruction}

Key context from the content:
{transcript[:500]}

Return ONLY the hook (1-3 short lines max). No explanation.""")
            ])
            
            result = await self.fast_llm.ainvoke(prompt.format_messages(
                big_idea=big_idea,
                framework=framework,
                instruction=instruction,
                transcript=transcript[:500],
                tone_profile=tone_profile
            ))
            
            return {
                "framework": framework,
                "hook": result.content.strip(),
                "description": instruction.split(" - ")[0]  # Short description
            }
        
        # Generate all hooks in parallel
        tasks = [
            generate_single_hook(framework, instruction)
            for framework, instruction in HOOK_FRAMEWORKS.items()
        ]
        
        hooks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any errors
        valid_hooks = [h for h in hooks if isinstance(h, dict)]
        
        logger.info(f"Generated {len(valid_hooks)} hook variants")
        return valid_hooks
