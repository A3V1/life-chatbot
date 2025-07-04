import json
import logging
from typing import Any, Dict, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from config import llm, retriever, RECOMMENDATION_PROMPT
from handlers.general_qa import handle_general_questions
from sqlconnect import get_policy_by_id, get_policy_by_name
from utils import clean_button_input
from handlers.closing import handle_application
logger = logging.getLogger(__name__)

def _safe_int_conversion(value: Any) -> Optional[int]:
    """Safely converts a value to an integer, returning None if conversion fails."""
    if value is None:
        return None
    try:
        return int(float(value))  # Use float conversion for robustness
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {value} (type: {type(value)}) to int. Returning None.")
        return None

def _safe_float_conversion(value: Any) -> Optional[float]:
    """Safely converts a value to a float, returning None if conversion fails."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {value} (type: {type(value)}) to float. Returning None.")
        return None


def _is_application_button(query: str) -> bool:
    """Check if user clicked an application button"""
    application_buttons = [
        "apply for",
    ]
    return any(button in query.lower() for button in application_buttons)

def _get_shown_recommendations(bot) -> list:
    """Safely retrieves shown_recommendations from context."""
    # Recommendations are now stored as a native list, not a JSON string.
    return bot.context.get("shown_recommendations", [])

def _extract_policy_id_from_button(query: str, bot) -> Optional[str]:
    shown = _get_shown_recommendations(bot)
    for item in shown:
        if item["name"].lower() in query.lower():
            return item["policy_id"]
    return None

def _extract_policy_name_from_query(query: str, bot) -> Optional[str]:
    shown = _get_shown_recommendations(bot)
    logger.debug(f"Shown recommendations in _extract_policy_name_from_query: {shown}")
    for item in shown:
        if item["name"].lower() in query.lower() or query.lower() in item["name"].lower():
            logger.debug(f"Found policy name '{item['name']}' in query '{query}'")
            return item["name"]
    logger.warning(f"Could not extract policy name from query: {query}")
    return None

def handle_recommendation_phase(bot, query: str) -> Dict[str, Any]:
    logger.debug(f"Entering handle_recommendation_phase with query: '{query}'")
    cleaned_query = clean_button_input(query)
    logger.debug(f"Cleaned query: '{cleaned_query}'")

    # State 1: Recommendations have been shown, user is taking action.
    if bot.context.get("shown_recommendations"):
        # Use the original query for routing, as cleaning might remove keywords.
        if _is_application_button(query):
            policy_id = _extract_policy_id_from_button(query, bot)
            bot._update_context({"selected_policy": policy_id, "context_state": "contact_capture"})
            # The main loop will now handle the transition to the application state
            return handle_application(bot, query)
        if "compare" in query.lower():
            return _compare_policies(bot)

        if "get more details" in query.lower():
            return _get_more_details(bot, query)
        
        if "details for" in cleaned_query.lower():
            policy_name = _extract_policy_name_from_query(cleaned_query, bot)
            if policy_name:
                return _get_details_by_policy_name(bot, policy_name)

        # Fallback to check if the query is an exact match for a policy name
        shown = _get_shown_recommendations(bot)
        for item in shown:
            if item["name"].lower() == cleaned_query.lower():
                return _get_details_by_policy_name(bot, item["name"])

        # If the user's query doesn't match any specific action, treat it as a general question.
        logger.warning(f"No matching action found for query: '{query}'. Treating as a general question.")
        return handle_general_questions(bot, query)

    # State 2: User has provided all info and is asking for recommendations.
    if query.strip().lower() in ["", "my profile is complete. please give me recommendations."]:
        if not bot._validate_context_completeness():
            return {"answer": "I need to collect a few more details before giving recommendations."}

        search_query = (
            f"{bot.context.get('primary_need')} insurance "
            f"for age {bot.context.get('age')} with income {bot.context.get('income')} "
            f"and budget {bot.context.get('budget')} for term {bot.context.get('term_length')} years "
            f"and coverage {bot.context.get('coverage_required')}."
        )

        user_age = _safe_int_conversion(bot.context.get("age"))
        user_budget = _safe_int_conversion(bot.context.get("budget"))
        user_term_length = _safe_int_conversion(bot.context.get("term_length"))
        user_coverage = _safe_int_conversion(bot.context.get("coverage_required"))

        logger.debug(f"User context: age={user_age}, income={bot.context.get('income')}, budget={user_budget}, term_length={user_term_length}, coverage_required={user_coverage}, primary_need={bot.context.get('primary_need')}")

        filters = {}
        if user_age:
            filters["entry_age_min"] = {"$lte": user_age}
            filters["entry_age_max"] = {"$gte": user_age}
        if user_budget:
            filters["premium"] = {"$lte": user_budget}
        if user_term_length:
            filters["policy_term_min"] = {"$lte": user_term_length}
            filters["policy_term_max"] = {"$gte": user_term_length}
        if user_coverage:
            filters["coverage_amount"] = {"$gte": user_coverage * 0.5, "$lte": user_coverage * 1.5}

        try:
            logger.debug(f"Invoking retriever with search_query: {search_query} and filters: {filters}")
            docs = retriever.invoke(search_query)
            logger.debug(f"Retriever returned {len(docs)} documents.")
        except Exception as e:
            logger.error(f"Error during retriever.invoke: {e}", exc_info=True)
            return {"answer": "I encountered an issue while searching for policies. Please try again later."}

        scored_policies = []
        for doc in docs:
            md = doc.metadata
            score = 0
            premium = _safe_float_conversion(md.get("premium"))
            coverage_amount = _safe_float_conversion(md.get("coverage_amount"))
            term_min = _safe_int_conversion(md.get("policy_term_min"))
            term_max = _safe_int_conversion(md.get("policy_term_max"))

            if user_budget and premium is not None:
                score += 10 if premium <= user_budget else -5
            if user_coverage and coverage_amount is not None:
                if user_coverage * 0.9 <= coverage_amount <= user_coverage * 1.1:
                    score += 10
                elif coverage_amount >= user_coverage:
                    score += 5
            if user_term_length and term_min is not None and term_max is not None:
                if term_min <= user_term_length <= term_max:
                    score += 10

            scored_policies.append({"doc": doc, "score": score})
        
        scored_policies.sort(key=lambda x: x["score"], reverse=True)
        top_policies = [item["doc"] for item in scored_policies[:2]]

        if not top_policies:
            return {"answer": "Sorry, I couldn't find policies that match your profile. Please try adjusting your criteria."}

        context_str = "\n\n".join([doc.page_content for doc in top_policies])
        user_info = json.dumps({
            "age": bot.context.get("age"), "income": bot.context.get("income"),
            "budget": bot.context.get("budget"), "term_length": bot.context.get("term_length"),
            "coverage_required": bot.context.get("coverage_required"), "primary_need": bot.context.get("primary_need")
        })

        try:
            llm_response_obj = llm.invoke(RECOMMENDATION_PROMPT.format(context=context_str, user_info=user_info, query=query))
            llm_response = llm_response_obj.content if hasattr(llm_response_obj, 'content') else str(llm_response_obj)
        except Exception as e:
            logger.error(f"Error during LLM invocation: {e}", exc_info=True)
            return {"answer": "I encountered an issue while generating recommendations. Please try again later."}

        structured_policies = [{"name": doc.metadata.get("policy_name", f"Policy {i+1}"), "policy_id": doc.metadata.get("policy_id", f"POLICY_{i+1}")} for i, doc in enumerate(top_policies)]
        
        bot._update_context({
            "shown_recommendations": structured_policies, # Store as a native list
            "retrieved_docs": [doc.page_content for doc in top_policies], # Store as a native list
            "context_state": "recommendation_given_phase"
        })

        options = [f"Apply for {item['name']}" for item in structured_policies] + ["Get More Details"]

        return {"answer": llm_response, "options": options}

    # Fallback for any other queries in this phase.
    return handle_general_questions(bot, query)

def _get_more_details(bot, query) -> Dict[str, Any]:
    """Asks the user to clarify which policy they want details about."""
    logger.debug(f"Entering _get_more_details with query: {query}")
    
    # Clear previous document context to prevent general QA from interfering
    bot.context.pop("retrieved_docs", None)
    
    shown = _get_shown_recommendations(bot)
    
    # If no policy is specified, ask the user to choose
    options = [f"Details for {item['name']}" for item in shown]
    options.append("Compare Policies")

    return {
        "answer": "Which policy would you like to get more details about?",
        "options": options
    }
    
def _get_details_by_policy_name(bot, policy_name: str) -> Dict[str, Any]:
    logger.debug(f"Entering _get_details_by_policy_name with policy_name: {policy_name}")
    
    if policy_name:
        policy_details = get_policy_by_name(policy_name)
        logger.debug(f"Policy details from DB for '{policy_name}': {policy_details}")
        
        if policy_details:
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
            ]
            
            details_list = []
            for key, title in display_keys:
                if key in policy_details and policy_details[key] is not None:
                    value = policy_details[key]
                    # Format currency values
                    if 'coverage' in key or 'premium' in key:
                        value = f"₹{value:,.0f}"
                    details_list.append(f"**{title}**: {value}")
            
            details_str = "\n".join(details_list)
            
            answer = (
                f"Here are the key details for **{policy_name}** from our policy catalog:\n\n"
                f"{details_str}"
            )
            return {"answer": answer}
        else:
            logger.warning(f"Could not find details for policy: {policy_name}")
            return {"answer": f"Sorry, I couldn't find details for {policy_name}."}
            
    logger.warning("policy_name was not provided to _get_details_by_policy_name.")
    return {"answer": "Sorry, I couldn't identify which policy you're asking about."}

def _compare_policies(bot) -> Dict[str, Any]:
    logger.debug("Entering _compare_policies")
    shown = _get_shown_recommendations(bot)
    if len(shown) < 2:
        logger.debug("Not enough policies to compare.")
        return {"answer": "Not enough policies to compare. Please ask for recommendations first."}

    policy1_id, policy2_id = shown[0]["policy_id"], shown[1]["policy_id"]
    policy1_name, policy2_name = shown[0]["name"], shown[1]["name"]

    policy1_details = get_policy_by_id(policy1_id)
    policy2_details = get_policy_by_id(policy2_id)

    if not policy1_details or not policy2_details:
        return {"answer": "Sorry, I couldn't retrieve the details for comparison."}

    excluded_keys = {'policy_id', 'id', 'description', 'company_name', 'policy_name'}
    
    # Correctly perform set difference before converting to list
    combined_keys = (set(policy1_details.keys()) | set(policy2_details.keys())) - excluded_keys
    all_keys = sorted(list(combined_keys))

    comparison_lines = [f"**Comparison between _{policy1_name}_ and _{policy2_name}_:**\n"]

    for key in all_keys:
        title = key.replace("_", " ").title()
        val1 = str(policy1_details.get(key, "N/A"))
        val2 = str(policy2_details.get(key, "N/A"))
        comparison_lines.append(f"• **{title}**\n  - {policy1_name}: {val1}\n  - {policy2_name}: {val2}")

    return {"answer": "\n".join(comparison_lines)}
