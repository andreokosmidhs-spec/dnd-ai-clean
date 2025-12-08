"""
Narration Filter - Enforces Human DM Filter v2 rules
Post-processes LLM output to ensure compliance

THIS FILTER IS MANDATORY FOR ALL NARRATION OUTPUT
"""
import logging
import re
from functools import wraps

logger = logging.getLogger(__name__)


def filter_narration(func):
    """
    Decorator to automatically filter any function that returns narration
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # If result is a dict with 'narration' key, filter it
        if isinstance(result, dict) and 'narration' in result:
            original = result['narration']
            result['narration'] = NarrationFilter.apply_filter(original)
            logger.info(f"🎭 Auto-filtered narration in {func.__name__}")
        
        return result
    return wrapper


class NarrationFilter:
    """Enforces narration quality rules"""
    
    # Banned phrases from Human DM Filter v2
    BANNED_PHRASES = [
        "you see", "you notice", "you realize", "you feel a sense",
        "it seems that", "it appears that", "in this moment", "as you look",
        "before you know it", "for a moment", "for a brief moment",
        "somehow", "seemingly", "moments later", "suddenly",
        "in front of you", "you get the sense", "you hear the sound of",
        "the area around you is", "you can't help but feel",
        "your heart pounds", "your breath catches", "an ominous presence",
        "tendrils of darkness", "shrouded in mystery"
    ]
    
    @staticmethod
    def count_sentences(text: str) -> int:
        """
        Count sentences in text
        
        Sentences end with: . ! ?
        """
        # Split by sentence terminators
        sentences = re.split(r'[.!?]+', text)
        # Filter out empty strings
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)
    
    @staticmethod
    def enforce_sentence_limit(text: str, max_sentences: int = 4) -> str:
        """
        Enforce maximum sentence limit
        
        If text exceeds limit, truncate to first N sentences
        """
        # Split into sentences
        sentences = re.split(r'([.!?]+)', text)
        
        # Rebuild with terminators
        full_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if sentences[i].strip():
                full_sentences.append(sentences[i].strip() + sentences[i+1])
        
        # Handle last sentence if no terminator
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            full_sentences.append(sentences[-1].strip() + '.')
        
        if len(full_sentences) <= max_sentences:
            return text
        
        # Truncate to max_sentences
        truncated = ' '.join(full_sentences[:max_sentences])
        logger.warning(f"⚠️ Narration truncated from {len(full_sentences)} to {max_sentences} sentences")
        return truncated
    
    @staticmethod
    def remove_banned_phrases(text: str) -> str:
        """
        Remove or replace banned phrases
        """
        result = text
        changes_made = []
        
        for phrase in NarrationFilter.BANNED_PHRASES:
            if phrase.lower() in result.lower():
                # Remove the phrase
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                result = pattern.sub('', result)
                changes_made.append(phrase)
        
        # Clean up double spaces and awkward punctuation
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\s+([.,;:!?])', r'\1', result)
        result = result.strip()
        
        if changes_made:
            logger.info(f"🚫 Removed banned phrases: {', '.join(changes_made[:3])}")
        
        return result
    
    @staticmethod
    def detect_novel_style(text: str) -> bool:
        """
        Detect if text is written in novel style
        
        Indicators:
        - Very long sentences (50+ words)
        - Stacked metaphors
        - Excessive adjectives
        """
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 50:
                return True
        
        # Check for stacked sensory descriptions
        sensory_words = ['scent', 'smell', 'sight', 'sound', 'taste', 'feel', 'touch']
        sensory_count = sum(1 for word in sensory_words if word in text.lower())
        if sensory_count > 2:
            return True
        
        return False
    
    # Context-specific sentence limits from v4.1 spec
    SENTENCE_LIMITS = {
        "intro": 16,
        "exploration": 10,
        "social": 10,
        "investigation": 10,
        "combat": 8,
        "travel": 8,
        "rest": 8,
        "downtime": 8,
        "unknown": 10  # Safe default
    }
    
    @staticmethod
    def apply_filter(narration: str, max_sentences: int = None, context: str = "unknown") -> str:
        """
        Apply all filters to narration
        
        Args:
            narration: Text to filter
            max_sentences: Maximum allowed sentences (if None, uses context-based limit from v4.1 spec)
            context: Where this narration came from (for logging and determining sentence limit)
                     Valid contexts: "intro", "exploration", "social", "investigation", "combat", "travel", "rest", "downtime"
        
        Returns: Cleaned narration text
        """
        if not narration or not narration.strip():
            return narration
        
        original_length = len(narration)
        original_sentences = NarrationFilter.count_sentences(narration)
        
        # Step 1: Remove banned phrases
        narration = NarrationFilter.remove_banned_phrases(narration)
        
        # Step 2: Determine sentence limit
        if max_sentences is None:
            # Use context-based limit from v4.1 spec
            max_sentences = NarrationFilter.SENTENCE_LIMITS.get(context.lower(), NarrationFilter.SENTENCE_LIMITS["unknown"])
            logger.info(f"📏 Using v4.1 sentence limit for [{context}]: {max_sentences} sentences")
        
        # Step 3: Enforce sentence limit (CRITICAL)
        narration = NarrationFilter.enforce_sentence_limit(narration, max_sentences=max_sentences)
        
        # Step 4: Check for novel style (log warning)
        if NarrationFilter.detect_novel_style(narration):
            logger.warning(f"⚠️ Novel-style narration in [{context}]")
        
        final_length = len(narration)
        final_sentences = NarrationFilter.count_sentences(narration)
        
        if final_length < original_length or final_sentences < original_sentences:
            reduction_pct = int(((original_length - final_length) / original_length) * 100) if original_length > 0 else 0
            logger.info(f"✂️ [{context}] {original_sentences}→{final_sentences} sentences, {reduction_pct}% reduction")
        
        return narration
