import re
from typing import Any, Dict
from sqlconnect import create_lead

# --- Phase 3: Structured Closing ---

def handle_application(bot, query: str) -> Dict[str, Any]:
    policy_id = bot.context.get("selected_policy")
    
    # Get the name of the selected policy from context
    policy_name = "the selected policy"
    if bot.context.get("shown_recommendations"):
        for policy in bot.context["shown_recommendations"]:
            if policy["policy_id"] == policy_id:
                policy_name = policy["name"]
                break

    bot._update_context({"context_state": "contact_capture"})
    return {"answer": f"Great! To start your application for **{policy_name}**, I need your full name."}

def handle_contact_capture(bot, query: str) -> Dict[str, Any]:
    if len(query.strip()) > 2:
        bot._update_context({
            "name": query.strip(),
            "context_state": "email_capture"
        })
        return {"answer": "Thanks! Now, could you provide your email address?"}
    return {"answer": "Please provide your full name."}

def handle_email_capture(bot, query: str) -> Dict[str, Any]:
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
    if email_match:
        email = email_match.group(0)
        name = bot.context.get("name", "").strip()
        bot._update_context({
            "email": email,
            "context_state": "follow_up"
        })

        create_lead(
            user_id=bot.user_id,
            name=name,
            policy_id=bot.context.get("selected_policy"),
            contact_method="email",
            contact_value=email
        )

        return {
            "answer": f"Thank you, {name}! A confirmation has been sent to {email}. Our team will contact you shortly."
        }

    return {"answer": "Please provide a valid email address (e.g., you@example.com)."}
