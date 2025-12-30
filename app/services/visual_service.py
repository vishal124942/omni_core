import os
import logging
import json
import asyncio
import base64
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Optional

import requests
from PIL import Image, ImageDraw, ImageFont
import img2pdf
from playwright.async_api import async_playwright
from openai import AsyncOpenAI
from rembg import remove

logger = logging.getLogger(__name__)

class VisualIntelligenceService:
    """
    Phase 1: Visual Intelligence (The Eye)
    Handles LinkedIn Carousels and AI Thumbnail generation.
    """
    
    OUTPUT_DIR = Path("./data/visuals")
    TEMPLATES_DIR = Path("./app/templates/visuals")
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Ensure directories exist
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize default fonts (standard ones)
        self.bold_font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if not os.path.exists(self.bold_font_path):
            self.bold_font_path = None # Fallback to default
            
    # --- LinkedIn Carousel Factory ---
    
    async def batch_generate_carousels(self, client_id: str, title: str, slides: List[str], styles: List[str]) -> Dict[str, dict]:
        """
        Generate multiple carousel styles in parallel using a SINGLE browser instance.
        This is much faster and lighter than launching 3 separate browsers.
        """
        logger.info(f"Batch generating carousels for {client_id} with styles: {styles}")
        
        results = {}
        
        # Pre-generate HTMLs (fast, CPU only)
        html_tasks = []
        for style in styles:
            html_template = self._get_carousel_template(title, slides, style)
            temp_html_path = self.OUTPUT_DIR / f"carousel_{client_id}_{style}.html"
            with open(temp_html_path, "w") as f:
                f.write(html_template)
            html_tasks.append((style, temp_html_path))

        async with async_playwright() as p:
            # 1. Launch ONE Browser (Heavy op)
            browser = await p.chromium.launch()
            
            # 2. Create parallel pages context (Light op)
            async def process_style(style, html_path):
                try:
                    page = await browser.new_page(viewport={"width": 1080, "height": 1080})
                    await page.goto(f"file://{html_path.absolute()}")
                    
                    # Wait for render
                    await page.wait_for_selector("#slide-0", state="visible")
                    await page.wait_for_timeout(300) # Jitter wait
                    
                    image_paths = []
                    for i in range(len(slides) + 2):
                        slide_id = f"#slide-{i}"
                        slide_path = self.OUTPUT_DIR / f"slide_{client_id}_{style}_{i}.png"
                        
                        element = await page.query_selector(slide_id)
                        if element:
                            await element.screenshot(path=str(slide_path))
                            image_paths.append(str(slide_path))
                        
                    await page.close()
                    
                    if not image_paths:
                        raise ValueError("No slides generated")
                        
                    # Merge to PDF
                    output_pdf_path = self.OUTPUT_DIR / f"carousel_{client_id}_{style}.pdf"
                    with open(output_pdf_path, "wb") as f:
                        f.write(img2pdf.convert(image_paths))
                        
                    return {
                        "pdf": f"/data/visuals/{output_pdf_path.name}",
                        "images": [f"/data/visuals/{Path(p).name}" for p in image_paths]
                    }
                except Exception as e:
                    logger.error(f"Error processing style {style}: {e}")
                    return {"error": str(e)}

            # 3. Run all pages in parallel
            tasks = [process_style(style, path) for style, path in html_tasks]
            batch_results = await asyncio.gather(*tasks)
            
            for style, res in zip(styles, batch_results):
                results[style] = res
                
            await browser.close()
            
        return results

    async def generate_linkedin_carousel(self, client_id: str, title: str, slides: List[str], style: str = "cyberpunk") -> str:
        """
        Convert text takes into a branded PDF carousel.
        
        Args:
            client_id: Client identifier
            title: Title for the carousel
            slides: List of strings (each a slide's content)
            style: "cyberpunk", "minimalist", or "corporate"
            
        Returns:
            Absolute path to the generated PDF
        """
        logger.info(f"Generating LinkedIn carousel for {client_id} with style {style}")
        
        # 1. Create temporary HTML file with the branded template
        html_template = self._get_carousel_template(title, slides, style)
        import uuid
        unique_id = f"{client_id}_{style}_{uuid.uuid4().hex[:8]}"
        temp_html_path = self.OUTPUT_DIR / f"carousel_{unique_id}.html"
        
        with open(temp_html_path, "w") as f:
            f.write(html_template)
            
        # 2. Use Playwright to take screenshots of each slide
        output_pdf_path = self.OUTPUT_DIR / f"carousel_{unique_id}.pdf"
        image_paths = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1080, "height": 1080})
            await page.goto(f"file://{temp_html_path.absolute()}")
            
            # Wait for any animations/rendering - wait for the first slide to be visible
            await page.wait_for_selector("#slide-0", state="visible")
            
            # Small jitter wait for fonts/styles
            await page.wait_for_timeout(300)
            
            for i in range(len(slides) + 2): # Cover + Content Slides + Conclusion
                slide_id = f"#slide-{i}"
                # Fix: Include style in filename to prevent parallel processes overwriting each other's screenshots
                slide_path = self.OUTPUT_DIR / f"slide_{client_id}_{style}_{i}.png"
                
                element = await page.query_selector(slide_id)
                if element:
                    await element.screenshot(path=str(slide_path))
                    image_paths.append(str(slide_path))
                
            await browser.close()
            
        if not image_paths:
            raise ValueError(f"Failed to generate any slides for style {style}. Check HTML rendering.")
            
        # 3. Merge PNGs into PDF
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
            
        # Cleanup
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
        logger.info(f"Carousel generated at {output_pdf_path}")
        return {
            "pdf": f"/data/visuals/{output_pdf_path.name}",
            "images": [f"/data/visuals/{Path(p).name}" for p in image_paths]
        }

    def _get_carousel_template(self, title: str, slides: List[str], style: str) -> str:
        """Helper to generate HTML/CSS for the carousel."""
        # Cyberpunk colors: Cyan (#00f3ff), Magenta (#ff00ff), Yellow (#ffff00)
        # Minimalist: White/Black/Gray
        # Corporate: Blue/Navy/White
        
        styles = {
            "cyberpunk": {
                "bg": "radial-gradient(circle, #0d0d0d 0%, #000000 100%)",
                "text": "#ffffff",
                "accent": "#00f3ff",
                "secondary": "#ff00ff",
                "border": "2px solid #00f3ff"
            },
            "minimalist": {
                "bg": "#ffffff",
                "text": "#000000",
                "accent": "#666666",
                "secondary": "#999999",
                "border": "1px solid #000000"
            },
            "corporate": {
                "bg": "#f4f7f9",
                "text": "#1a365d",
                "accent": "#3182ce",
                "secondary": "#2c5282",
                "border": "5px solid #3182ce"
            }
        }
        
        s = styles.get(style, styles["cyberpunk"])
        
        # Build HTML with each slide as a div
        slides_html = []
        
        # Cover Slide
        slides_html.append(f"""
            <div id="slide-0" class="slide cover">
                <div class="glow"></div>
                <h1 style="color: {s['accent']}">{title}</h1>
                <p>A Deep Dive with Omni-Core Agent</p>
                <div class="footer">SWIPE LEFT &rarr;</div>
            </div>
        """)
        
        # Content Slides
        for i, text in enumerate(slides):
            slides_html.append(f"""
                <div id="slide-{i+1}" class="slide content">
                    <div class="number">{i+1}</div>
                    <div class="card">
                        <p>{text}</p>
                    </div>
                </div>
            """)
            
        # Conclusion Slide
        slides_html.append(f"""
            <div id="slide-{len(slides)+1}" class="slide conclusion">
                <h2 style="color: {s['secondary']}">Ready to Scale?</h2>
                <p>Check the link in comments for the full video.</p>
                <div class="cta">LIKE &bull; REPOST &bull; FOLLOW</div>
            </div>
        """)
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@400;700&display=swap" rel="stylesheet">
            <style>
                body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
                .slide {{ 
                    width: 1080px; 
                    height: 1080px; 
                    display: flex; 
                    flex-direction: column; 
                    justify-content: center; 
                    align-items: center; 
                    padding: 80px; 
                    box-sizing: border-box;
                    background: {s['bg']};
                    color: {s['text']};
                    position: relative;
                    overflow: hidden;
                }}
                h1 {{ font-family: 'Orbitron', sans-serif; font-size: 84px; text-transform: uppercase; text-align: center; margin-bottom: 20px; text-shadow: 0 0 20px {s['accent']}44; }}
                h2 {{ font-size: 64px; text-transform: uppercase; }}
                p {{ font-size: 42px; line-height: 1.4; text-align: center; max-width: 800px; }}
                .number {{ position: absolute; top: 40px; right: 40px; font-size: 120px; font-weight: bold; opacity: 0.1; font-family: 'Orbitron'; color: {s['accent']}; }}
                .card {{ border: {s['border']}; padding: 60px; border-radius: 24px; background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); }}
                .glow {{ position: absolute; width: 400px; height: 400px; background: {s['accent']}11; border-radius: 50%; filter: blur(80px); top: -100px; left: -100px; }}
                .footer {{ position: absolute; bottom: 60px; font-weight: bold; font-family: 'Orbitron'; letter-spacing: 4px; color: {s['secondary']}; }}
                .cta {{ margin-top: 40px; font-size: 24px; font-family: 'Orbitron'; opacity: 0.8; letter-spacing: 2px; }}
            </style>
        </head>
        <body>
            {''.join(slides_html)}
        </body>
        </html>
        """
        return full_html

    # --- Thumbnail A/B Generator ---

    async def generate_thumbnail_variants(self, transcript: str, user_image_path: Optional[str] = None) -> List[str]:
        """
        Generate 3 distinct YouTube thumbnails based on content.
        
        Args:
            transcript: Video transcript
            user_image_path: Optional path to user's headshot for cutouts
            
        Returns:
            List of absolute paths to generated thumbnails
        """
        logger.info("Generating 3 thumbnail variants via DALL-E 3")
        
        # 1. Ask GPT-4o to describe 3 high-CTR scenes with catchphrases
        prompts_res = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Return a JSON with 3 image prompts and 3 short catchphrases (max 10 chars each). Example: {'variants': [{'prompt': '...', 'text': 'MISTAKE!'}, ...]}"},
                {"role": "user", "content": f"TRANSCRIPT: {transcript[:2000]}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        data = json.loads(prompts_res.choices[0].message.content)
        variants = data.get("variants", [])[:3]
        
        # 2. Parallelize thumbnail generation
        tasks = [
            self._generate_single_thumbnail(f"thumbnail_{i}", v["prompt"], v["text"], user_image_path)
            for i, v in enumerate(variants)
        ]
        
        results = await asyncio.gather(*tasks)
        return results

    async def _generate_single_thumbnail(self, name: str, prompt: str, overlay_text: str, user_image_path: Optional[str]) -> str:
        """Helper to generate and composite a single thumbnail."""
        
        # 1. Generate Base Image via DALL-E 2 (Faster)
        response = await self.client.images.generate(
            model="dall-e-2",
            prompt=f"Cinematic YouTube thumbnail background, high contrast, vibrant: {prompt}. Vivid colors. No text.",
            n=1,
            size="512x512" # DALL-E 2 fast generation
        )
        
        image_url = response.data[0].url
        img_data = requests.get(image_url).content
        base_img = Image.open(BytesIO(img_data)).resize((1280, 720))
        
        # 2. Add User Face Cutout (Optional)
        if user_image_path and os.path.exists(user_image_path):
            try:
                with open(user_image_path, "rb") as i:
                    input_img = i.read()
                    output_img = remove(input_img)
                    face_cutout = Image.open(BytesIO(output_img))
                    
                    # Resize and paste face
                    face_cutout.thumbnail((600, 600))
                    base_img.paste(face_cutout, (20, 120), face_cutout)
            except Exception as e:
                logger.warning(f"Failed to process face cutout: {str(e)}")

        # 3. Add Massive Bold Text with Pillow
        draw = ImageDraw.Draw(base_img)
        
        # Try to find a thick font
        font_size = 180
        try:
            if self.bold_font_path:
                font = ImageFont.truetype(self.bold_font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            
        # Add stroke for readability
        text_pos = (640, 360) # Center-ish
        # Calculate text size to center it properly
        # For simplicity, we just draw at a fixed spot or right-aligned
        
        # Draw stroke
        stroke_width = 8
        for offset in range(-stroke_width, stroke_width + 1):
            draw.text((800 + offset, 450), overlay_text, font=font, fill="black")
            draw.text((800, 450 + offset), overlay_text, font=font, fill="black")
            
        draw.text((800, 450), overlay_text, font=font, fill="yellow")
        
        output_path = self.OUTPUT_DIR / f"{name}_final.png"
        base_img.save(output_path)
        
        return f"/data/visuals/{output_path.name}"
