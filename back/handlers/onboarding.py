from typing import Any, Dict
from utils import clean_button_input, extract_numeric_value

# --- Phase 1: Structured Onboarding ---
def handle_get_primary_need(bot, query: str) -> Dict[str, Any]:
    if query:
        cleaned_query = clean_button_input(query)
        bot._update_context({"primary_need": cleaned_query, "context_state": "get_insurance_goal"})
        return handle_get_insurance_goal(bot, "")
    return {
        "answer": "Welcome! To find the best policy, let's start with your primary goal.",
        "options": ["Family Protection", "Tax Savings", "Investment", "Retirement Planning"],
    }

def handle_get_insurance_goal(bot, query: str) -> Dict[str, Any]:
    if query:
        cleaned_query = clean_button_input(query)
        bot._update_context({"insurance_goal": cleaned_query, "context_state": "collect_age"})
        return handle_collect_age(bot, "")
    return {
        "answer": "What is the main purpose of this insurance?",
        "options": ["Child's Education", "Leave a Legacy", "Loan Protection", "Wealth Creation"],
    }

def handle_collect_age(bot, query: str) -> Dict[str, Any]:
    if query:
        age = extract_numeric_value(query, "age")
        if age:
            bot._update_context({"age": age, "context_state": "collect_income"})
            return handle_collect_income(bot, "")
        return {"answer": "That doesn't look right. Please enter a valid age (e.g., 35)."}
    return {"answer": "Got it. What is your current age?"}

def handle_collect_income(bot, query: str) -> Dict[str, Any]:
    if query:
        income = extract_numeric_value(query, "income")
        if income:
            bot._update_context({"income": income, "context_state": "collect_budget"})
            return handle_collect_budget(bot, "")
        return {"answer": "Please enter a valid annual income (e.g., 10 lakhs or 1000000)."}
    return {"answer": "Thanks. What is your approximate annual income?"}

def handle_collect_budget(bot, query: str) -> Dict[str, Any]:
    if query:
        budget = extract_numeric_value(query, "budget")
        if budget:
            bot._update_context({"budget": budget, "context_state": "collect_term_length"})
            return handle_collect_term_length(bot, "")
        return {"answer": "Please provide a valid monthly budget (e.g., 5000)."}
    return {"answer": "And what is your comfortable monthly budget for the premium?"}

def handle_collect_term_length(bot, query: str) -> Dict[str, Any]:
    if query:
        term = extract_numeric_value(query, "term")
        if term:
            bot._update_context({"term_length": term, "context_state": "collect_coverage"})
            return handle_collect_coverage(bot, "")
        return {"answer": "Please provide a valid term in years (e.g., 20)."}
    return {"answer": "For how many years do you need the policy to cover you?"}

def handle_collect_coverage(bot, query: str) -> Dict[str, Any]:
    if query:
        coverage = extract_numeric_value(query, "coverage")
        if coverage:
            bot._update_context({"coverage_required": coverage, "context_state": "recommendation_given_phase"})
            # Use a local import to avoid circular dependency
            from .recommendation import handle_recommendation_phase
            return handle_recommendation_phase(bot, "My profile is complete. Please give me recommendations.")
        return {"answer": "Please provide a valid coverage amount (e.g., 50 lakhs or 5000000)."}
    return {"answer": "Finally, how much coverage are you looking for?"}
