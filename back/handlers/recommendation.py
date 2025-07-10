import json
import logging
from typing import Any, Dict, Optional
from langchain_core.prompts import PromptTemplate
from config import llm, retriever, RECOMMENDATION_PROMPT
from handlers.general_qa import handle_general_questions
from sqlconnect import get_policy_by_id, get_policy_by_name
from utils import clean_button_input

logger = logging.getLogger(__name__)

def _clean_llm_response(response_content: str) -> str:
    """Extracts a JSON object from a string, even if it's embedded in other text."""
    # Find the start and end of the JSON object
    start_index = response_content.find('{')
    end_index = response_content.rfind('}')
    
    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = response_content[start_index:end_index+1]
        return json_str
    
    # Fallback for markdown fences if the above fails
    cleaned_content = response_content.strip()
    if cleaned_content.startswith("```json"):
        cleaned_content = cleaned_content[7:]
    if cleaned_content.endswith("```"):
        cleaned_content = cleaned_content[:-3]
    
    return cleaned_content.strip()

def _is_get_quotation_button(query: str) -> bool:
    """Check if user clicked get quotation button"""
    return "get quotation" in query.lower()

def _is_show_details_button(query: str) -> bool:
    """Check if user clicked show details button"""
    return "show details" in query.lower() or "more details" in query.lower()

def _is_ask_general_questions_button(query: str) -> bool:
    """Check if user clicked ask general questions button"""
    return "ask general questions" in query.lower() or "general questions" in query.lower()

def handle_recommendation_phase(bot, query: str) -> Dict[str, Any]:
    """Handles the initial recommendation and subsequent user interactions."""
    cleaned_query = clean_button_input(query)

    if bot.context.get("context_state") == "recommendation_given_phase":
        if _is_get_quotation_button(query):
            # The policy is already selected, just transition the state
            bot._update_context({
                "context_state": "generate_premium_quotation"  # Transition to the form trigger
            })
            return {}  # The handler for this state will trigger the form
        if _is_show_details_button(query):
            return _get_more_details(bot)
        
        if _is_ask_general_questions_button(query):
            # Transition to general questions phase         
            return {"answer": "Sure! What would you like to know?"}
        
        # After providing details, offer the same options again
        if bot.context.get("last_action") == "provided_details":
            options = ["Get Quotation", "Show Details"]
            bot.context["last_action"] = None  # Reset flag
            return {"answer": "What would you like to do next?", "options": options}

        return handle_general_questions(bot, query)

    if not bot._validate_context_completeness():
        return {"answer": "I need a bit more information to give you a recommendation."}

    search_query = f"insurance for person {bot.context.get('existing_policy')} and {bot.context.get('employment_status')} with annual income {bot.context.get('annual_income')}"
    docs = retriever.invoke(search_query)
    
    if not docs:
        logger.warning(f"No policies found for query: '{search_query}'. Falling back to generic search.")
        docs = retriever.invoke("insurance policy") # Fallback query
        if not docs:
            logger.error("Fallback failed: No policies found in the vector store at all.")
            return {"answer": "I'm sorry, I couldn't find any policies right now. Please try again later."}

    top_policy = docs[0]
    logging.debug(f"Retrieved document: {top_policy}")
    # Truncate the context to avoid exceeding token limits
    context_str = top_policy.page_content[:250]  # ~125 tokens
    user_info_dict = {
        "existing_policy": bot.context.get("existing_policy"),
        "annual_income": bot.context.get("annual_income"),
        "employment_status": bot.context.get("employment_status")
    }

    prompt = RECOMMENDATION_PROMPT.format(
        context=context_str,
        user_info=user_info_dict,
        query=query
    )

    # Optional logging
    logger.debug(f"Prompt length: {len(prompt)} chars")

    llm_response = llm.invoke(prompt)
    
    try:
        cleaned_response = _clean_llm_response(llm_response.content)
        structured_policy = json.loads(cleaned_response)
        
        policy_name = structured_policy.get('name')
        if not policy_name:
            raise KeyError("LLM response did not include a policy name.")

        # Fetch the policy from the database to get the correct policy_id
        db_policy = get_policy_by_name(policy_name)
        if not db_policy:
            logger.error(f"Policy '{policy_name}' recommended by LLM not found in the database.")
            return {"answer": "I found a suitable policy, but I'm having trouble retrieving its details. Please try again."}

        policy_id = db_policy.get('policy_id')
        
        bot._update_context({
            "context_state": "recommendation_given_phase",
            "shown_recommendations": [structured_policy], # Still show the LLM's description
            "selected_policy": policy_id,
            "selected_policy_type": policy_name
        })
        
        # Provide the two specific options you want
        options = ["Get Quotation", "Show Details", "Ask General Questions"]
        
        answer = f"Based on your profile, I recommend the **{structured_policy['name']}**."
        if structured_policy.get('description'):
            answer += f"\n\n{structured_policy['description']}"

        return {"answer": answer, "options": options}
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error processing recommendation response: {e}\nResponse: {llm_response.content}")
        return {"answer": "I'm ware having trouble processing the recommendation details. Could you please try asking again?"}

def _get_more_details(bot) -> Dict[str, Any]:
    """Provides more details about the recommended policy from the database."""
    policy_id = bot.context.get("selected_policy")
    if not policy_id:
        return {"answer": "I'm sorry, I don't have a selected policy to show details for."}

    # Fetch details directly from the database
    policy_details = get_policy_by_id(policy_id)
    if not policy_details:
        logger.warning(f"Could not find details for policy ID: {policy_id}")
        return {"answer": f"Sorry, I couldn't find the details for that policy."}

    # Define which details to show and in what order
    display_keys = [
        ("policy_name", "Policy Name"),
        ("provider_name", "Provider"),
        ("policy_type", "Type"),
        ("coverage_max", "Maximum Coverage"),
        ("premium_max", "Maximum Premium"),
        ("age_max", "Maximum Entry Age"),
        ("claim_settlement_ratio", "Claim Settlement Ratio"),
        ("tax_benefits", "Tax Benefits"),
        ("benefits", "Benefits"),
    ]
    
    details_list = []
    for key, title in display_keys:
        if key in policy_details and policy_details[key] is not None:
            value = policy_details[key]
            # Format currency values
            if 'coverage' in key or 'premium' in key:
                if isinstance(value, (int, float)):
                    value = f"₹{value:,.0f}"
            details_list.append(f"**{title}**: {value}")
    
    details_str = "\n".join(details_list)
    
    answer = (
        f"Here are the key details for **{policy_details.get('policy_name', 'N/A')}**:\n\n"
        f"{details_str}"
    )

    bot._update_context({"last_action": "provided_details"})
    return {"answer": answer}
