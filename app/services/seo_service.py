"""
SEO Service - Heuristic scoring and optimization for blog content.
Grades articles against SEO best practices and can auto-optimize.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SEOScore:
    """SEO scoring result."""
    score: int
    max_score: int
    grade: str
    feedback: list[str]
    details: dict


class SEOService:
    """Service for SEO analysis and optimization of blog content."""
    
    # SEO scoring rubric
    RUBRIC = {
        "has_h1": {"points": 15, "check": "H1 heading present"},
        "has_h2s": {"points": 10, "check": "H2 subheadings present"},
        "word_count_ok": {"points": 15, "check": "Word count 800-1500"},
        "reading_level": {"points": 15, "check": "Grade 8 or below reading level"},
        "keyword_in_title": {"points": 10, "check": "Keyword in title"},
        "keyword_in_first_100": {"points": 10, "check": "Keyword in first 100 words"},
        "has_conclusion": {"points": 10, "check": "Has conclusion section"},
        "has_cta": {"points": 10, "check": "Has call-to-action"},
        "short_paragraphs": {"points": 5, "check": "Paragraphs are short (under 150 words)"},
    }
    
    def __init__(self):
        """Initialize SEO service."""
        self.max_score = sum(r["points"] for r in self.RUBRIC.values())
    
    def score_article(self, content: str, keyword: Optional[str] = None) -> SEOScore:
        """
        Score an article against SEO best practices.
        
        Args:
            content: Article content in markdown
            keyword: Optional target keyword to check for
            
        Returns:
            SEOScore with detailed breakdown
        """
        score = 0
        feedback = []
        details = {}
        
        # Auto-extract keyword if not provided
        if not keyword:
            keyword = self._extract_likely_keyword(content)
        
        # 1. Check H1
        has_h1 = content.strip().startswith("# ")
        if has_h1:
            score += self.RUBRIC["has_h1"]["points"]
            details["has_h1"] = True
        else:
            feedback.append("❌ Add an H1 heading (# Title) at the start")
            details["has_h1"] = False
        
        # 2. Check H2s
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        if h2_count >= 3:
            score += self.RUBRIC["has_h2s"]["points"]
            details["h2_count"] = h2_count
        else:
            feedback.append(f"❌ Add more H2 sections ({h2_count} found, need 3+)")
            details["h2_count"] = h2_count
        
        # 3. Word count
        word_count = len(content.split())
        if 800 <= word_count <= 1500:
            score += self.RUBRIC["word_count_ok"]["points"]
            details["word_count"] = word_count
        else:
            if word_count < 800:
                feedback.append(f"❌ Article too short ({word_count} words, need 800+)")
            else:
                feedback.append(f"⚠️ Article may be too long ({word_count} words)")
            details["word_count"] = word_count
        
        # 4. Reading level (simplified check)
        avg_word_length = sum(len(w) for w in content.split()) / max(word_count, 1)
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = word_count / max(len(sentences), 1)
        
        # Flesch-Kincaid approximation
        grade_level = 0.39 * avg_sentence_length + 11.8 * (avg_word_length / 4.5) - 15.59
        
        if grade_level <= 8:
            score += self.RUBRIC["reading_level"]["points"]
            details["reading_grade"] = round(grade_level, 1)
        else:
            feedback.append(f"❌ Simplify language (Grade {round(grade_level, 1)}, aim for 8)")
            details["reading_grade"] = round(grade_level, 1)
        
        # 5. Keyword in title
        if keyword:
            first_line = content.split('\n')[0].lower()
            if keyword.lower() in first_line:
                score += self.RUBRIC["keyword_in_title"]["points"]
                details["keyword_in_title"] = True
            else:
                feedback.append(f"❌ Add keyword '{keyword}' to the title")
                details["keyword_in_title"] = False
            
            # 6. Keyword in first 100 words
            first_100 = ' '.join(content.split()[:100]).lower()
            if keyword.lower() in first_100:
                score += self.RUBRIC["keyword_in_first_100"]["points"]
                details["keyword_early"] = True
            else:
                feedback.append(f"❌ Include keyword '{keyword}' in first 100 words")
                details["keyword_early"] = False
        
        # 7. Has conclusion
        has_conclusion = bool(re.search(r'##?\s*(conclusion|wrap|summary|final)', content, re.I))
        if has_conclusion:
            score += self.RUBRIC["has_conclusion"]["points"]
            details["has_conclusion"] = True
        else:
            feedback.append("❌ Add a Conclusion section")
            details["has_conclusion"] = False
        
        # 8. Has CTA
        cta_patterns = [
            r'subscribe', r'sign up', r'download', r'learn more',
            r'get started', r'join', r'contact', r'try', r'read more'
        ]
        has_cta = any(re.search(p, content, re.I) for p in cta_patterns)
        if has_cta:
            score += self.RUBRIC["has_cta"]["points"]
            details["has_cta"] = True
        else:
            feedback.append("❌ Add a call-to-action (e.g., 'Subscribe for more')")
            details["has_cta"] = False
        
        # 9. Short paragraphs
        paragraphs = re.split(r'\n\n+', content)
        long_paragraphs = sum(1 for p in paragraphs if len(p.split()) > 150)
        if long_paragraphs == 0:
            score += self.RUBRIC["short_paragraphs"]["points"]
            details["short_paragraphs"] = True
        else:
            feedback.append(f"⚠️ Break up {long_paragraphs} long paragraph(s)")
            details["short_paragraphs"] = False
        
        # Calculate grade
        percentage = (score / self.max_score) * 100
        if percentage >= 80:
            grade = "A"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 40:
            grade = "C"
        else:
            grade = "D"
        
        return SEOScore(
            score=score,
            max_score=self.max_score,
            grade=grade,
            feedback=feedback if feedback else ["✅ All SEO checks passed!"],
            details=details
        )
    
    def _extract_likely_keyword(self, content: str) -> str:
        """Extract the most likely target keyword from content."""
        # Get first H1 or first line
        first_line = content.split('\n')[0]
        first_line = re.sub(r'^#\s*', '', first_line)  # Remove markdown heading
        
        # Get significant words
        words = re.findall(r'\b[a-z]{4,}\b', first_line.lower())
        
        # Filter common words
        stop_words = {'this', 'that', 'with', 'from', 'your', 'have', 'will', 'what', 'when', 'where', 'about'}
        words = [w for w in words if w not in stop_words]
        
        return words[0] if words else ""
    
    def get_optimization_prompt(self, content: str, score_result: SEOScore) -> str:
        """
        Generate a prompt to optimize the content based on feedback.
        
        Args:
            content: Original content
            score_result: SEO score with feedback
            
        Returns:
            Optimization prompt for GPT
        """
        if score_result.score >= 80:
            return ""  # No optimization needed
        
        feedback_str = "\n".join(f"- {f}" for f in score_result.feedback if f.startswith("❌"))
        
        return f"""
Rewrite this blog post to fix these SEO issues:

{feedback_str}

ORIGINAL POST:
{content}

INSTRUCTIONS:
- Fix each issue listed above
- Keep the same topic and main points
- Maintain professional tone
- Ensure word count is 1000+ words
- Add a clear conclusion with CTA

Return the improved post in markdown format.
"""
