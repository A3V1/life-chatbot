import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_base_rate(plan_option: str) -> float:
    """Returns a base rate depending on the savings plan type."""
    plan_option = plan_option.lower()
    if "wealth" in plan_option:
        return 0.0012
    elif "child" in plan_option:
        return 0.0014
    elif "retirement" in plan_option:
        return 0.0013
    elif "monthly" in plan_option:
        return 0.0015
    elif "endowment" in plan_option:
        return 0.0011
    else:
        return 0.0012 # Default

def get_term_adj(policy_term: int) -> float:
    """Returns a term adjustment factor."""
    if policy_term <= 10:
        return 1.05
    elif policy_term <= 20:
        return 1.0
    else:
        return 0.95

def get_premium_term_discount(premium_payment_term: int, policy_term: int) -> float:
    """Returns a discount for shorter payment terms."""
    if premium_payment_term < policy_term:
        return 0.9 # 10% discount for limited pay
    return 1.0

def get_payout_modifier(payout_frequency: str) -> float:
    """Returns a modifier based on payout frequency."""
    payout_frequency = payout_frequency.lower()
    if "monthly" in payout_frequency:
        return 1.1  # Higher cost for monthly payouts
    elif "quarterly" in payout_frequency:
        return 1.075
    elif "half-yearly" in payout_frequency:
        return 1.05
    elif "yearly" in payout_frequency:
        return 1.025
    elif "lump sum" in payout_frequency:
        return 1.0
    else:
        return 1.05  # Default for any other case

def calculate_age(dob: str) -> int:
    """Calculate age from date of birth string (YYYY-MM-DD)."""
    try:
        birth_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except (ValueError, TypeError):
        return 30 # Default age if DOB is invalid

def calculate_premium(
    plan_option: str,
    policy_term: int,
    premium_payment_term: int,
    payout_frequency: str,
    dob: str,
    coverage: float = None,
    budget: float = None,
) -> dict:
    """
    Calculates premium for savings plans.
    Can be driven by desired coverage or affordable budget.
    """
    if not (coverage or budget):
        return {"error": "Either coverage or budget must be provided."}

    # Calculate adjustments
    base_rate = get_base_rate(plan_option)
    term_adj = get_term_adj(policy_term)
    payment_adj = get_premium_term_discount(premium_payment_term, policy_term)
    payout_adj = get_payout_modifier(payout_frequency)
    
    # Simplified age factor
    age = calculate_age(dob)
    age_factor = 1 + ((age - 30) / 100) # Simple linear adjustment based on age 30

    # Combine all factors
    combined_factor = base_rate * term_adj * payment_adj * payout_adj * age_factor

    if coverage:
        # Coverage-driven calculation
        base_premium = coverage * combined_factor
        sum_assured = coverage
    else:
        # Budget-driven calculation
        base_premium = budget
        # Reverse calculate the estimated coverage
        sum_assured = budget / combined_factor if combined_factor > 0 else 0

    gst = base_premium * 0.18
    total_premium = base_premium + gst

    return {
        "sum_assured": round(sum_assured, 2),
        "base_premium": round(base_premium, 2),
        "gst": round(gst, 2),
        "total_premium": round(total_premium, 2),
    }
