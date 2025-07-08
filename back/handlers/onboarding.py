from typing import Any, Dict
from sqlconnect import update_user_context, update_user_info, get_user_by_id
from utils import clean_button_input

# --- Phase 1: Structured Onboarding ---

def handle_existing_policy(bot, query: str) -> Dict[str, Any]:
    """Asks the user if they have an existing policy."""
    name = get_user_by_id(bot.user_id).get("name", "User")
    if query:
        cleaned_query = clean_button_input(query)
        bot._update_context({
            "existing_policy": cleaned_query,
            "context_state": "collect_employment_status"
        })
        update_user_info(bot.user_id, {"existing_policy": cleaned_query})
        # Proceed to collect employment status
        return handle_employment_status(bot, "")
    
    return {
        "answer": f"Welcome, {name}! To help you find the best-fit insurance plan, I have a few quick questions.",
        "options": ["I have an existing policy", "I do not have an existing policy"],
    }

def handle_employment_status(bot, query: str) -> Dict[str, Any]:
    """Collects the user's employment status."""
    if query:
        cleaned_query = clean_button_input(query)
        bot._update_context({
            "employment_status": cleaned_query,
            "context_state": "collect_annual_income"
        })
        # Also update the user_info table
        update_user_info(bot.user_id, {"employment_status": cleaned_query})
        return handle_annual_income(bot, "")
    
    return {
        "answer": "What is your current employment status?",
        "options": ["Salaried", "Self-Employed", "Other"],
        # "input_type": "dropdown"  # Specify dropdown for the frontend
    }

def handle_annual_income(bot, query: str) -> Dict[str, Any]:
    """Collects the user's annual income."""
    if query:
        cleaned_query = clean_button_input(query)
        # Convert to a numeric value for the database
        income_map = {
            "Less than 5 Lakhs": 400000,
            "5-10 Lakhs": 750000,
            "10-20 Lakhs": 1500000,
            "20+ Lakhs": 2500000,
        }
        income_value = income_map.get(cleaned_query, 0)
        
        bot._update_context({
            "annual_income": cleaned_query,
            "context_state": "recommendation_phase"  # End of onboarding
        })
        # Also update the user_info table
        update_user_info(bot.user_id, {"annual_income": income_value})
        
        # Check if context is complete before moving to recommendation
        if bot._validate_context_completeness():
            # Use a local import to avoid circular dependency
            from .recommendation import handle_recommendation_phase
            return handle_recommendation_phase(bot, "My profile is complete. Please give me recommendations.")
        else:
            # This should not happen if the flow is correct, but as a fallback
            return {"answer": "I still need a few more details. Let's continue."}
    
    return {
        "answer": "What is your approximate annual income?",
        "options": ["Less than 5 Lakhs", "5-10 Lakhs", "10-20 Lakhs", "20+ Lakhs"],
        # "input_type": "dropdown"  # Specify dropdown for the frontend
    }
