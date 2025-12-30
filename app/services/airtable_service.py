"""
Airtable service for storing generated content.
"""

import os
import logging
from typing import Optional, Any

from pyairtable import Api, Table

from app.models.schemas import ContentOutput

logger = logging.getLogger(__name__)


class AirtableService:
    """Service for storing content assets in Airtable."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_id: Optional[str] = None,
        table_name: Optional[str] = None
    ):
        """
        Initialize Airtable service.
        
        Args:
            api_key: Airtable API key. If not provided, reads from AIRTABLE_API_KEY env var.
            base_id: Airtable base ID. If not provided, reads from AIRTABLE_BASE_ID env var.
            table_name: Table name. If not provided, reads from AIRTABLE_TABLE_NAME env var.
        """
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        self.table_name = table_name or os.getenv("AIRTABLE_TABLE_NAME", "ContentAssets")
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY is required")
        if not self.base_id:
            raise ValueError("AIRTABLE_BASE_ID is required")
        
        self.api = Api(self.api_key)
        self.table = self.api.table(self.base_id, self.table_name)
    
    def create_record(
        self,
        client_id: str,
        content: ContentOutput,
        video_url: str
    ) -> dict[str, Any]:
        """
        Create a new record with generated content.
        
        Args:
            client_id: Client identifier
            content: Generated content output
            video_url: Original video URL
            
        Returns:
            Created record data including ID and URL
        """
        try:
            # Prepare fields for Airtable
            fields = {
                "Client_ID": client_id,
                "Status": "Completed",
                "Video_URL": str(video_url),
                "Big_Idea": content.analysis.big_idea,
                "Tone": content.analysis.tone,
                "Strong_Takes": "\n\n".join(
                    f"{i+1}. {take}" 
                    for i, take in enumerate(content.analysis.strong_takes)
                ),
                "LinkedIn_Draft": content.linkedin_post,
                "Twitter_Thread": self._format_twitter_thread(content.twitter_thread),
                "Blog_HTML": content.blog_post,
            }
            
            # Add new production feature fields
            if content.linkedin_hooks:
                fields["LinkedIn_Hooks"] = "\n\n".join(
                    f"[{h.get('framework', 'Unknown')}] {h.get('hook', '')}" for h in content.linkedin_hooks
                )
            
            if content.seo_score:
                fields["SEO_Score"] = f"{content.seo_score.get('grade', 'N/A')} ({content.seo_score.get('score', 0)})"
                fields["SEO_Feedback"] = "\n".join(content.seo_score.get('feedback', []))
            
            if content.broll_images:
                # Save as single text block (for new column)
                fields["B_Roll_Images"] = "\n".join(
                    f"{img.get('keyword', 'Image')}: {img.get('image_url', '')}" for img in content.broll_images
                )
                # ALSO map to legacy Clip columns (so they appear in existing table)
                for i, img in enumerate(content.broll_images[:3]):
                    fields[f"Clip_{i+1}_URL"] = img.get('image_url', '')
            
            if content.newsletter_html:
                fields["Newsletter_HTML"] = content.newsletter_html[:100000]  # Airtable cell limit
            
            # Try to create the record with all fields
            try:
                record = self.table.create(fields)
            except Exception as e:
                # If it fails (likely due to missing columns), try fallback
                if "422" in str(e) or "Unknown field" in str(e):
                    logger.warning("Failed to save all fields. Retrying with core fields only. Please add missing columns to Airtable.")
                    
                    # Filter to only core fields + legacy clip fields (which exist)
                    core_fields = {
                        k: v for k, v in fields.items() 
                        if k in [
                            "Client_ID", "Status", "Video_URL", "Big_Idea", 
                            "Tone", "Strong_Takes", "LinkedIn_Draft", 
                            "Twitter_Thread", "Blog_HTML",
                            "Clip_1_URL", "Clip_2_URL", "Clip_3_URL"
                        ]
                    }
                    record = self.table.create(core_fields)
                else:
                    raise e
            
            record_id = record.get("id", "")
            record_url = self._build_record_url(record_id)
            
            logger.info(f"Created Airtable record: {record_id}")
            
            return {
                "id": record_id,
                "url": record_url,
                "fields": record.get("fields", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to create Airtable record: {str(e)}")
            # Don't raise, just return error info so pipeline continues
            return {
                "id": "",
                "url": "",
                "error": str(e)
            }
    
    def update_record_status(self, record_id: str, status: str) -> None:
        """
        Update the status of an existing record.
        
        Args:
            record_id: Airtable record ID
            status: New status value
        """
        try:
            self.table.update(record_id, {"Status": status})
            logger.info(f"Updated record {record_id} status to: {status}")
        except Exception as e:
            logger.error(f"Failed to update record status: {str(e)}")
            raise
    
    def _format_twitter_thread(self, tweets: list[str]) -> str:
        """
        Format Twitter thread for storage.
        
        Args:
            tweets: List of tweet texts
            
        Returns:
            Formatted thread string
        """
        formatted = []
        for i, tweet in enumerate(tweets):
            formatted.append(f"Tweet {i+1}/{len(tweets)}:\n{tweet}")
        return "\n\n---\n\n".join(formatted)
    
    def _build_record_url(self, record_id: str) -> str:
        """
        Build the Airtable record URL.
        
        Args:
            record_id: Airtable record ID
            
        Returns:
            Full URL to the record
        """
        return f"https://airtable.com/{self.base_id}/{self.table_name}/{record_id}"
