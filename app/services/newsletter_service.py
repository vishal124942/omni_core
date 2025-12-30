"""
Newsletter Service - HTML Email Builder.
Generates ready-to-send HTML emails from generated content.
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Beautiful HTML email template
NEWSLETTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        /* Reset */
        body, table, td, p, a, li {{ margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        
        /* Container */
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; }}
        
        /* Header */
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; }}
        .header h1 {{ color: #ffffff; font-size: 24px; margin: 0; font-weight: 700; }}
        
        /* Video Section */
        .video-section {{ padding: 30px; text-align: center; background: #f8f9fa; }}
        .video-thumbnail {{ position: relative; display: inline-block; }}
        .video-thumbnail img {{ max-width: 100%; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }}
        .play-button {{ 
            position: absolute; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%);
            width: 70px;
            height: 70px;
            background: rgba(255,255,255,0.95);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .play-button::after {{
            content: '';
            border-left: 25px solid #667eea;
            border-top: 15px solid transparent;
            border-bottom: 15px solid transparent;
            margin-left: 5px;
        }}
        
        /* Content */
        .content {{ padding: 40px 30px; }}
        .big-idea {{ 
            font-size: 22px; 
            font-weight: 700; 
            color: #1a1a2e; 
            line-height: 1.4;
            margin-bottom: 25px;
            padding-bottom: 25px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        /* Key Takeaways */
        .takeaways {{ margin: 30px 0; }}
        .takeaways h2 {{ font-size: 18px; color: #667eea; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }}
        .takeaway-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .takeaway-number {{
            background: #667eea;
            color: #fff;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            margin-right: 15px;
            flex-shrink: 0;
        }}
        .takeaway-text {{ color: #333; font-size: 15px; line-height: 1.5; }}
        
        /* CTA Button */
        .cta-section {{ text-align: center; padding: 20px 30px 40px; }}
        .cta-button {{
            display: inline-block;
            padding: 16px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 30px;
            font-weight: 700;
            font-size: 16px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        
        /* Footer */
        .footer {{
            background: #1a1a2e;
            padding: 30px;
            text-align: center;
        }}
        .footer p {{ color: #888; font-size: 13px; line-height: 1.6; }}
        .footer a {{ color: #667eea; text-decoration: none; }}
        
        /* Responsive */
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .content, .header, .footer {{ padding: 25px 20px !important; }}
        }}
    </style>
</head>
<body style="background-color: #f4f4f4; padding: 20px;">
    <table role="presentation" class="container" cellpadding="0" cellspacing="0" width="600" style="margin: 0 auto;">
        <!-- Header -->
        <tr>
            <td class="header">
                <h1>🎬 New Video Breakdown</h1>
            </td>
        </tr>
        
        <!-- Video Thumbnail -->
        <tr>
            <td class="video-section">
                <a href="{video_url}" class="video-thumbnail" target="_blank">
                    <img src="{thumbnail_url}" alt="Watch Video" width="540">
                    <div class="play-button"></div>
                </a>
            </td>
        </tr>
        
        <!-- Main Content -->
        <tr>
            <td class="content">
                <p class="big-idea">💡 {big_idea}</p>
                
                <div class="takeaways">
                    <h2>🔑 Key Takeaways</h2>
                    {takeaways_html}
                </div>
            </td>
        </tr>
        
        <!-- CTA -->
        <tr>
            <td class="cta-section">
                <a href="{video_url}" class="cta-button" target="_blank">
                    ▶️ Watch Full Video
                </a>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td class="footer">
                <p>You received this email because you subscribed to our content updates.</p>
                <p style="margin-top: 10px;">
                    <a href="#">Unsubscribe</a> · <a href="#">Preferences</a>
                </p>
                <p style="margin-top: 15px; color: #666;">© {year} Content Repurposing Engine</p>
            </td>
        </tr>
    </table>
</body>
</html>
"""


class NewsletterService:
    """Service for generating HTML email newsletters."""
    
    def __init__(self):
        """Initialize Newsletter service."""
        pass
    
    def generate_html(
        self,
        big_idea: str,
        strong_takes: list[str],
        video_url: str,
        thumbnail_url: Optional[str] = None,
        subject: Optional[str] = None
    ) -> str:
        """
        Generate a ready-to-send HTML email newsletter.
        
        Args:
            big_idea: Main insight from the video
            strong_takes: Key takeaways
            video_url: Link to the original video
            thumbnail_url: Video thumbnail image URL
            subject: Email subject line
            
        Returns:
            Complete HTML email string
        """
        # Generate thumbnail if not provided
        if not thumbnail_url:
            thumbnail_url = self._get_youtube_thumbnail(video_url)
        
        # Build takeaways HTML
        takeaways_html = ""
        for i, take in enumerate(strong_takes[:5], 1):  # Max 5 takeaways
            takeaways_html += f"""
                <div class="takeaway-item">
                    <span class="takeaway-number">{i}</span>
                    <span class="takeaway-text">{take}</span>
                </div>
            """
        
        # Generate subject if not provided
        if not subject:
            subject = f"🎬 {big_idea[:50]}..." if len(big_idea) > 50 else f"🎬 {big_idea}"
        
        # Fill template
        html = NEWSLETTER_TEMPLATE.format(
            subject=subject,
            video_url=video_url,
            thumbnail_url=thumbnail_url or "https://via.placeholder.com/540x300/667eea/ffffff?text=Watch+Video",
            big_idea=big_idea,
            takeaways_html=takeaways_html,
            year=datetime.now().year
        )
        
        logger.info("Generated newsletter HTML")
        return html
    
    def _get_youtube_thumbnail(self, video_url: str) -> str:
        """
        Extract YouTube video thumbnail URL.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Thumbnail URL
        """
        import re
        
        patterns = [
            r'(?:v=|/embed/|/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                video_id = match.group(1)
                return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        return "https://via.placeholder.com/540x300/667eea/ffffff?text=Watch+Video"
    
    def generate_plain_text(
        self,
        big_idea: str,
        strong_takes: list[str],
        video_url: str
    ) -> str:
        """
        Generate plain text version of the newsletter.
        
        Args:
            big_idea: Main insight
            strong_takes: Key takeaways
            video_url: Video link
            
        Returns:
            Plain text email content
        """
        takeaways = "\n".join(f"  {i}. {take}" for i, take in enumerate(strong_takes, 1))
        
        return f"""
🎬 NEW VIDEO BREAKDOWN
========================

💡 THE BIG IDEA:
{big_idea}

🔑 KEY TAKEAWAYS:
{takeaways}

▶️ WATCH THE FULL VIDEO:
{video_url}

---
You received this email because you subscribed to our content updates.
Unsubscribe: [link]
"""
