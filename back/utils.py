import re
import logging
from typing import Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)

def clean_button_input(text: str) -> str:
    """Removes leading numbers and whitespace from button selections."""
    return re.sub(r"^\d+\.\s*", "", text).strip()

def extract_numeric_value(text: str, field_name: str) -> Optional[int]:
    if not text or not isinstance(text, str): return None
    try:
        clean_text = re.sub(r"[₹,rs,rupees,lakhs,lakh,crores,crore,cr]", "", text.lower()).strip()
        multiplier = 1
        if "lakh" in text.lower(): multiplier = 100000
        elif "crore" in text.lower() or "cr" in text.lower(): multiplier = 10000000
        
        match = re.search(r"(\d+\.?\d*)", clean_text)
        if match:
            value = int(float(match.group(1)) * multiplier)
            # Apply specific validations based on field name
            if field_name == "age":
                return value if 18 <= value <= 80 else None
            if field_name == "income":
                return value if value >= 50000 else None
            if field_name == "budget":
                return value if value >= 500 else None
            if field_name == "term":
                return value if 1 <= value <= 50 else None
            if field_name == "coverage":
                return value if value >= 100000 else None
            
            # If field_name is generic (like 'amount'), return the value directly
            return value
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not extract numeric value for '{field_name}' from text: '{text}'. Error: {e}")
    return None

def is_general_question(query: str, specific_keywords: list[str] = None) -> bool:
    """
    Detects if a user's query is a general question using boundary-aware checks.
    It ignores specific command keywords relevant to the current state.
    """
    if not isinstance(query, str):
        return False
    lower_query = query.lower().strip()
    specific_keywords = specific_keywords or []

    # If the query contains a state-specific keyword (as a whole word), it's not a general question.
    for keyword in specific_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', lower_query):
            logger.debug(f"Query '{lower_query}' matched specific keyword '{keyword}'. Not a general question.")
            return False

    # If the query is very short and purely numeric, it's likely a direct answer.
    if lower_query.isnumeric() and len(lower_query) < 5:
        logger.debug(f"Query '{lower_query}' is short and numeric. Not a general question.")
        return False

    # Define keywords that strongly indicate a general or subjective question.
    question_keywords = [
        "what", "who", "where", "when", "why", "how", "can you", "tell me",
        "explain", "is there", "difference", "recommend", "which is better",
        "should i", "do you think", "what is"
    ]

    # Check if the query contains any of the question keywords (as whole words) or a question mark.
    if '?' in lower_query:
        logger.debug(f"Query '{lower_query}' contains '?'. Is a general question.")
        return True
    
    for keyword in question_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', lower_query):
            logger.debug(f"Query '{lower_query}' matched general keyword '{keyword}'. Is a general question.")
            return True

    logger.debug(f"Query '{lower_query}' did not match any general question criteria.")
    return False

def generate_quote_number():
    """Generates a unique quote number."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_digits = random.randint(1000, 9999)
    return f"QUOTE-{timestamp}-{random_digits}"
