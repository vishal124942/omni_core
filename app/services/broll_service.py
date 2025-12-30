"""
B-Roll Service - Automatic image matching for content.
Uses Pexels API to fetch royalty-free images based on content keywords.
"""

import os
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class BRollService:
    """Service for fetching relevant B-roll images from Pexels."""
    
    PEXELS_API_URL = "https://api.pexels.com/v1"
    
    # Keyword extraction patterns
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "can", "need", "dare", "ought", "used", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into",
        "through", "during", "before", "after", "above", "below",
        "between", "under", "again", "further", "then", "once",
        "here", "there", "when", "where", "why", "how", "all",
        "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than",
        "too", "very", "just", "and", "but", "if", "or", "because",
        "until", "while", "about", "against", "between", "into",
        "through", "during", "before", "after", "above", "below",
        "this", "that", "these", "those", "i", "you", "he", "she",
        "it", "we", "they", "what", "which", "who", "whom"
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize B-Roll service.
        
        Args:
            api_key: Pexels API key. Reads from PEXELS_API_KEY env if not provided.
        """
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        
        if not self.api_key:
            logger.warning("PEXELS_API_KEY not set - B-roll images will be skipped")
        
        self.headers = {"Authorization": self.api_key} if self.api_key else {}
    
    async def get_images_for_content(
        self,
        strong_takes: list[str],
        per_take: int = 1
    ) -> list[dict]:
        """
        Fetch relevant images for each strong take.
        
        Args:
            strong_takes: List of strong take statements
            per_take: Number of images per take
            
        Returns:
            List of image data dicts
        """
        if not self.api_key:
            logger.info("Skipping B-roll - no API key")
            return []
        
        images = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for take in strong_takes:
                keyword = self._extract_keyword(take)
                
                if not keyword:
                    continue
                
                try:
                    response = await client.get(
                        f"{self.PEXELS_API_URL}/search",
                        params={"query": keyword, "per_page": per_take, "orientation": "landscape"},
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        photos = data.get("photos", [])
                        
                        if photos:
                            photo = photos[0]
                            images.append({
                                "strong_take": take,
                                "keyword": keyword,
                                "image_url": photo["src"]["medium"],
                                "image_large": photo["src"]["large"],
                                "photographer": photo["photographer"],
                                "pexels_url": photo["url"],
                                "alt": photo.get("alt", keyword)
                            })
                            logger.info(f"Found image for keyword: {keyword}")
                    else:
                        logger.warning(f"Pexels API error: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Failed to fetch image for '{keyword}': {str(e)}")
        
        return images
    
    def _extract_keyword(self, text: str) -> str:
        """
        Extract the most relevant keyword from text.
        
        Args:
            text: Input text to extract keyword from
            
        Returns:
            Single keyword string
        """
        # Clean text
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        # Filter stop words and short words
        keywords = [
            w for w in words 
            if w not in self.STOP_WORDS and len(w) > 3
        ]
        
        if not keywords:
            return ""
        
        # Return the longest word (often most specific)
        return max(keywords, key=len)
    
    async def get_video_thumbnail(self, video_url: str) -> Optional[str]:
        """
        Get thumbnail image for a YouTube video.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Thumbnail URL or None
        """
        import re
        
        # Extract video ID
        patterns = [
            r'(?:v=|/embed/|/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                video_id = match.group(1)
                # YouTube provides thumbnails at predictable URLs
                return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        return None
