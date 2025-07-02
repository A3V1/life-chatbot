import re
from typing import Optional

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
            if field_name == "age": return value if 18 <= value <= 80 else None
            if field_name == "income": return value if value >= 50000 else None
            if field_name == "budget": return value if value >= 500 else None
            if field_name == "term": return value if 1 <= value <= 50 else None
            if field_name == "coverage": return value if value >= 100000 else None
    except (ValueError, AttributeError): pass
    return None
