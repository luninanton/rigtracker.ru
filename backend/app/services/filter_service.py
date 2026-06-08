import re
from typing import Tuple, Optional, List
from config import settings


def classify_and_filter_tender(
    title: str, 
    description: str,
    keywords: Optional[List[str]] = None,
    minus_words: Optional[List[str]] = None
) -> Tuple[Optional[str], str]:
    """
    Analyzes title and description.
    Returns: (machinery_type, status)
    - If minus-words are detected, status is "Архив".
    - Otherwise, status is "Новый".
    """
    text_to_check = f"{title or ''} {description or ''}"
    
    kw_list = keywords if keywords is not None else settings.KEYWORDS
    mw_list = minus_words if minus_words is not None else settings.MINUS_WORDS
    
    # 1. Check minus words (case-insensitive)
    for minus_word in mw_list:
        if re.search(r'\b' + re.escape(minus_word.strip()) + r'\b', text_to_check, re.IGNORECASE):
            return None, "Архив"
            
    # 2. Check keywords (case-insensitive) to identify machinery type
    machinery_type = None
    for keyword in kw_list:
        if re.search(r'\b' + re.escape(keyword.strip()) + r'\b', text_to_check, re.IGNORECASE):
            # Keep capitalized keyword as standard type
            machinery_type = keyword.strip()
            break
            
    return machinery_type, "Новый"

def calculate_scout_score(price_start: Optional[float], price_current: Optional[float]) -> float:
    """
    Calculates scout score based on price drop discount.
    If price_current is lower than price_start, score is the percentage drop.
    """
    if not price_start or not price_current or price_start <= 0:
        return 0.0
    if price_current >= price_start:
        return 0.0
    
    discount = ((price_start - price_current) / price_start) * 100
    return round(discount, 2)
