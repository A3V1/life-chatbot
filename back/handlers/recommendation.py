import json
from typing import Any, Dict
from langchain_core.output_parsers import StrOutputParser
from config import llm, retriever, RECOMMENDATION_PROMPT
from utils import clean_button_input
from sqlconnect import get_policy_by_name

def _is_application_button(query: str) -> bool:
    """Check if user clicked an application button"""
    application_buttons = [
        "apply for",
    ]
    return any(button in query.lower() for button in application_buttons)

def _extract_policy_from_button(query: str, bot) -> str:
    shown = json.loads(bot.context.get("shown_recommendations", "[]"))
    for item in shown:
        if item["name"].lower() in query.lower():
            return item["name"]
    return "Selected Policy"

def handle_recommendation_phase(bot, query: str) -> Dict[str, Any]:
    cleaned_query = clean_button_input(query)

    if _is_application_button(cleaned_query):
        policy_name = _extract_policy_from_button(cleaned_query, bot)
        bot._update_context({"selected_policy": policy_name, "context_state": "application"})
        from handlers.closing import handle_application
        return handle_application(bot, "")

    if "compare" in cleaned_query.lower():
        return _compare_policies(bot)

    if "details" in cleaned_query.lower():
        return _get_more_details(bot, query)

    
    if bot.context.get("shown_recommendations"):
        return {
            "answer": "I've already recommended some policies. What would you like to do next?",
            "options": ["Compare Policies", "Get More Details", "Apply for a Policy"]
        }

    if query.strip().lower() in ["", "my profile is complete. please give me recommendations."]:
        if not bot._validate_context_completeness():
            return {"answer": "I need to collect a few more details before giving recommendations."}

        search_query = (
            f"{bot.context.get('primary_need')} insurance "
            f"for age {bot.context.get('age')} with income {bot.context.get('income')} "
            f"and budget {bot.context.get('budget')} for term {bot.context.get('term_length')} years "
            f"and coverage {bot.context.get('coverage_required')}."
        )

        docs = retriever.invoke(search_query)
        top_policies = docs[:2]

        if not top_policies:
            return {"answer": "Sorry, I couldn't find policies that match your profile."}

        policy_summaries = []
        options = []
        structured_policies = []

        for i, doc in enumerate(top_policies, start=1):
            md = doc.metadata
            insurer_name = md.get("insurer_name", f"Policy {i}")
            policy_type = md.get("policy_type", "N/A")
            coverage = md.get("coverage_amount", "N/A")
            premium = md.get("premium", "N/A")

            summary = (
                f"**{insurer_name}** ({policy_type})\n"
                f"Coverage: ₹{coverage} | Annual Premium: ₹{premium}"
            )

            policy_summaries.append(summary)
            options.append(f"Apply for {insurer_name} ")
            structured_policies.append({
                "name": insurer_name,
                "policy_id": md.get("id", f"POLICY_{i}")
            })

        bot._update_context({
            "shown_recommendations": json.dumps(structured_policies),
            "retrieved_docs": json.dumps([doc.page_content for doc in top_policies]),
            "context_state": "recommendation_given_phase"
        })

        return {
            "answer": "Based on your profile, here are two suitable policy options:\n\n" + "\n\n".join(policy_summaries),
            "options": options + ["Compare Policies", "Get More Details", "Show Different Options"]
        }

    return _handle_policy_questions(bot, query)

def _get_more_details(bot, query) -> Dict[str, Any]:
    """Provides more details for a selected policy."""
    shown = json.loads(bot.context.get("shown_recommendations", "[]"))
    
    # Extract policy name from the query
    policy_name = None
    for item in shown:
        if item["name"].lower() in query.lower():
            policy_name = item["name"]
            break

    if policy_name:
        policy_details = get_policy_by_name(policy_name)
        if policy_details:
            details_str = "\n".join([f"**{key.replace('_', ' ').title()}**: {value}" for key, value in policy_details.items()])
            return {"answer": f"Here are more details for {policy_name}:\n\n{details_str}"}
        else:
            return {"answer": f"Sorry, I couldn't find details for {policy_name}."}

    # If no policy is specified, ask the user to choose
    options = [f"Details for {item['name']}" for item in shown]
    return {
        "answer": "Which policy would you like to get more details about?",
        "options": options
    }

# def _show_different_options(bot) -> Dict[str, Any]:
#     """Shows different policy options to the user."""
#     # This is a simple implementation that re-runs the recommendation.
#     # A more advanced version could alter the search query.
#     return handle_recommendation_phase(bot, "")

def _compare_policies(bot) -> Dict[str, Any]:
    """Generates a comparison of the shown policies."""
    shown = json.loads(bot.context.get("shown_recommendations", "[]"))
    if len(shown) < 2:
        return {"answer": "Not enough policies to compare. Please ask for recommendations first."}

    policy1_name = shown[0]["name"]
    policy2_name = shown[1]["name"]

    policy1_details = get_policy_by_name(policy1_name)
    policy2_details = get_policy_by_name(policy2_name)

    if not policy1_details or not policy2_details:
        return {"answer": "Sorry, I couldn't retrieve the details for comparison."}

    comparison = f"Here's a comparison of {policy1_name} and {policy2_name}:\n\n"
    
    details1_str = "\n".join([f"**{key.replace('_', ' ').title()}**: {value}" for key, value in policy1_details.items()])
    details2_str = "\n".join([f"**{key.replace('_', ' ').title()}**: {value}" for key, value in policy2_details.items()])

    comparison += f"**{policy1_name}**\n{details1_str}\n\n"
    comparison += f"**{policy2_name}**\n{details2_str}"

    return {"answer": comparison}

def _handle_policy_questions(bot, query: str) -> Dict[str, Any]:
    """Handle free text questions about policies"""
    
    # Simple response for policy questions
    answer = f"Based on your requirements, I can help answer that. {query}. The recommended policies are designed to fit your budget and coverage needs. Would you like to apply for any of these policies?"
    
    shown = json.loads(bot.context.get("shown_recommendations", "[]"))
    options = [f"Apply for {item['name']}" for item in shown]
    options.extend(["Compare Policies", "Get More Details", "Show Different Options"])

    return {
        "answer": answer,
        "options": options
    }
