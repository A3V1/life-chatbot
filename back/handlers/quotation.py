import logging
import json
from typing import Any, Dict
from config import llm
from sqlconnect import update_user_context, get_user_info_for_quote
from utils import generate_quote_number, get_persistent_actions
from premium_calculator import calculate_premium

logger = logging.getLogger(__name__)

def handle_generate_premium_quotation(bot, query: str) -> Dict[str, Any]:
    """
    Generates a friendly prompt to encourage the user to fill out the quotation form.
    """
    user_name = bot.context.get("name", "there")
    
    # Extract a simplified user profile for the prompt
    user_profile_items = {
        k: v for k, v in bot.context.items()
        if k in ["employment_status", "annual_income", "existing_policy", "plan_option"] and v is not None
    }
    user_profile = json.dumps(user_profile_items, default=str)
    
    prompt = f"""You are a friendly and encouraging insurance assistant. Your goal is to motivate the user to get a personalized quote.
    
    User's name: {user_name}
    User's profile highlights: {user_profile}

    The user is now at the stage of generating a premium quotation. Craft a short, welcoming message (under 30 words).
    - Address the user by name if available.
    - Briefly mention that the next step is to get a personalized quote.
    - Encourage them to fill out the form to see their customized options.
    - Maintain a positive and helpful tone.
    """
    
    try:
        llm_response = llm.invoke(prompt)
        answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
    except Exception as e:
        logging.error(f"Error in handle_generate_premium_quotation during LLM call: {e}", exc_info=True)
        answer = "Let's get you a personalized quote! Please fill out the form below to continue."

    return {
        "answer": answer,
        "input_type": "multi_step_form"
    }

def _safe_int_conversion(value: Any, default: int = 0) -> int:
    """Safely converts a value to an integer."""
    if value is None:
        return default
    try:
        if isinstance(value, str) and not value.isnumeric():
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

class QuotationHandler:
    def __init__(self, bot, user_id: int, context: Dict[str, Any]):
        self.bot = bot
        self.user_id = user_id
        self.context = context

    def handle(self) -> Dict[str, Any]:
        """
        Generates a premium quotation based on the user's context.
        This is called directly by the API endpoint.
        """
        logger.debug(f"--- Generating Premium Quotation for User ID: {self.user_id} ---")
        
        # Fetch the latest user data to ensure consistency
        db_user_info = get_user_info_for_quote(self.user_id) or {}
        final_context = {**self.context, **db_user_info}

        policy_term_val = _safe_int_conversion(final_context.get("policy_term"))
        premium_payment_term_val = _safe_int_conversion(final_context.get("premium_payment_term"))

        if final_context.get("premium_payment_term") == "Same as policy term":
            premium_payment_term_val = policy_term_val

        # Standardize keys and perform conversions up-front
        final_context["plan_type"] = final_context.get("plan_option") or final_context.get("plan_type")
        final_context["payout_frequency"] = final_context.get("income_payout_frequency") or final_context.get("payout_frequency")
        
        if final_context.get("premium_payment_term") == "Same as policy term":
            final_context["premium_payment_term"] = final_context.get("policy_term")

        policy_term_val = _safe_int_conversion(final_context.get("policy_term"))
        premium_payment_term_val = _safe_int_conversion(final_context.get("premium_payment_term"))

        premium_inputs = {
            "coverage": final_context.get("coverage_required"),
            "budget": final_context.get("premium_budget"),
            "plan_type": final_context.get("plan_type"),
            "policy_term": policy_term_val,
            "premium_payment_term": premium_payment_term_val,
            "payout_frequency": final_context.get("payout_frequency"),
            "dob": final_context.get("dob"),
        }
        logger.debug(f"Inputs for premium calculation: {premium_inputs}")

        required_keys = ["plan_type", "policy_term", "premium_payment_term", "payout_frequency", "dob"]
        missing_keys = [k for k in required_keys if not premium_inputs.get(k) and premium_inputs.get(k) != 0]
        has_financial_goal = final_context.get("coverage_required") or final_context.get("premium_budget")

        if missing_keys or not has_financial_goal:
            error_parts = []
            if missing_keys:
                # Create user-friendly names for missing keys
                friendly_names = {
                    "plan_type": "a plan type",
                    "policy_term": "a policy term",
                    "premium_payment_term": "a premium payment term",
                    "payout_frequency": "a payout frequency",
                    "dob": "your date of birth"
                }
                missing_friendly = [friendly_names.get(k, k) for k in missing_keys]
                error_parts.append(f"it looks like we still need {', '.join(missing_friendly)}")
            
            if not has_financial_goal:
                error_parts.append("you need to set a coverage amount")

            error_message = f"I'm sorry, I can't generate a quote just yet because {', and '.join(error_parts)}. Please fill out the form completely."
            logger.warning(f"Quotation failed. Missing keys: {missing_keys}, Has financial goal: {has_financial_goal}")
            return {"answer": error_message}

        premium_data = calculate_premium(**premium_inputs)
        if "error" in premium_data:
            logger.error(f"Premium calculation failed: {premium_data['error']}")
            return {"answer": f"I'm sorry, I couldn't generate a quote. {premium_data['error']}"}

        quote_num = generate_quote_number()
        
        quote_updates = {
            "quote_number": quote_num,
            "sum_assured": premium_data.get('sum_assured'),
            "base_premium": premium_data.get('base_premium'),
            "gst_amount": premium_data.get('gst'),
            "total_premium": premium_data.get('total_premium'),
            "premium_payment_frequency": final_context.get('premium_payment_frequency'),
            "context_state": "quote_displayed"
        }
        
        logger.debug(f"Updating user context with quote data: {quote_updates}")
        update_user_context(self.user_id, quote_updates)

        quote_data = {
            "quote_number": quote_num,
            "sum_assured": premium_data.get('sum_assured'),
            "policy_term": final_context.get('policy_term'),
            "premium_payment_term": final_context.get('premium_payment_term'),
            "base_premium": premium_data.get('base_premium'),
            "gst": premium_data.get('gst'),
            "total_premium": premium_data.get('total_premium'),
            "premium_frequency": final_context.get('premium_payment_frequency'),
            "plan_type": final_context.get("plan_type")
        }
        
        # Format the response for the chatbot
        answer_text = (
            f"Here is your personalized quote (Quote ID: {quote_num}):\n"
            f"- **Plan Selected:** {quote_data['plan_type']}\n"
            f"- **Sum Assured:** ₹{quote_data['sum_assured']:,.2f}\n"
            f"- **Policy Term:** {quote_data['policy_term']} years\n"
            f"- **Premium Payment Term:** {quote_data['premium_payment_term']} years\n"
            f"- **Premium:** ₹{quote_data['base_premium']:,.2f}\n"
            f"- **GST (18%):** ₹{quote_data['gst']:,.2f}\n"
            f"- **Total Payable Premium:** ₹{quote_data['total_premium']:,.2f} ({quote_data['premium_frequency']})"
        )

        actions = ["Proceed to Buy"] + get_persistent_actions(self.context)

        return {
            "answer": answer_text,
            "quote_data": quote_data,
            "actions": actions
        }
