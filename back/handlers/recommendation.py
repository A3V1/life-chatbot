import json
import logging
from typing import Any, Dict, Optional
from langchain_core.prompts import PromptTemplate
from config import llm, retriever, RECOMMENDATION_PROMPT
from handlers.general_qa import handle_general_questions
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

def _is_application_button(query: str) -> bool:
    """Check if user clicked an application button"""
    return "apply for" in query.lower()

def _get_shown_recommendations(bot) -> list:
    """Safely retrieves shown_recommendations from context."""
    return bot.context.get("shown_recommendations", [])

def _extract_policy_id_from_button(query: str, bot) -> Optional[str]:
    shown = _get_shown_recommendations(bot)
    for item in shown:
        if item["name"].lower() in query.lower():
            return item["policy_id"]
    return None

def handle_recommendation_phase(bot, query: str) -> Dict[str, Any]:
    """Handles the initial recommendation and subsequent user interactions."""
    cleaned_query = clean_button_input(query)

    if bot.context.get("context_state") == "recommendation_given_phase":
        if _is_application_button(query):
            policy_id = _extract_policy_id_from_button(query, bot)
            bot._update_context({
                "selected_policy": policy_id,
                "context_state": "generate_premium_quotation" # Transition directly to the form trigger
            })
            # The handler for 'generate_premium_quotation' will now trigger the form
            return {} # Return empty to trigger the state transition
        
        if "get more details" in query.lower():
            return _get_more_details(bot)
        
        # After providing details, offer the apply button again.
        if bot.context.get("last_action") == "provided_details":
             options = [f"Apply for {item['name']}" for item in _get_shown_recommendations(bot)]
             options.append("Ask another question")
             bot.context["last_action"] = None # Reset flag
             return {"answer": "What would you like to do next?", "options": options}

        return handle_general_questions(bot, query)

    if not bot._validate_context_completeness():
        return {"answer": "I need a bit more information to give you a recommendation."}

    search_query = f"insurance for {bot.context.get('employment_status')} with annual income {bot.context.get('annual_income')}"
    docs = retriever.invoke(search_query)
    
    if not docs:
        return {"answer": "Sorry, I couldn't find any policies matching your profile."}

    top_policy = docs[0]
    logging.debug(f"Retrieved document: {top_policy}")
    # Truncate the context to avoid exceeding token limits
    context_str = top_policy.page_content[:250]  # ~125 tokens
    user_info_dict = {
        "age": bot.context.get("age"),
        "annual_income": bot.context.get("annual_income"),
        "employment_status": bot.context.get("employment_status")
    }
    # user_info = json.dumps(user_info_dict)

    prompt = RECOMMENDATION_PROMPT.format(
        context=context_str,
        user_info=user_info_dict,
        query=query
    )

    # Optional logging
    logger.debug(f"Prompt length: {len(prompt)} chars")

    llm_response = llm.invoke(prompt)
    bot._update_context({
        "context_state": "recommendation_given_phase",  # Wait for user to apply or ask questions
        "shown_recommendations": []
    })

    try:
        cleaned_response = _clean_llm_response(llm_response.content)
        structured_policy = json.loads(cleaned_response)
        bot.context["shown_recommendations"] = [structured_policy]
        options = [f"Apply for {structured_policy['name']}", "Get More Details"]
        
        answer = f"Based on your profile, I recommend the **{structured_policy['name']}**."
        if structured_policy.get('description'):
            answer += f"\n\n{structured_policy['description']}"

        return {"answer": answer, "options": options}
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error processing recommendation response: {e}\nResponse: {llm_response.content}")
        return {"answer": "I'm having trouble processing the recommendation details. Could you please try asking again?"}

def _get_more_details(bot) -> Dict[str, Any]:
    """Asks the user to clarify which policy they want details about."""
    shown = _get_shown_recommendations(bot)
    options = [f"Details for {item['name']}" for item in shown]
    bot._update_context({"last_action": "provided_details"}) # Set flag
    return {
        "answer": "Which policy would you like to get more details about?",
        "options": options
    }
