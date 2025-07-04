import re
from typing import Any, Dict
from sqlconnect import create_lead

# --- Phase 3: Structured Closing ---
def handle_application(bot, query: str) -> Dict[str, Any]:
    policy_name = bot.context.get("selected_policy", "the selected policy")
    bot._update_context({"context_state": "contact_capture"})
    return {"answer": f"Great! To start your application, I need your full name."}

def handle_contact_capture(bot, query: str) -> Dict[str, Any]:
    if len(query) > 2:
        bot._update_context({"name": query, "context_state": "email_capture"})
        return handle_email_capture(bot, "")
    return {"answer": "Please provide your full name."}

def handle_email_capture(bot, query: str) -> Dict[str, Any]:
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
    if email_match:
        email = email_match.group(0)
        bot._update_context({"email": email, "context_state": "follow_up"})
        create_lead(
            user_id=bot.user_id,
            policy_id=bot.context.get("selected_policy"),
            contact_method="email",
            contact_value=email
        )
        return {"answer": f"Thank you, {bot.context.get('name')}! A confirmation will be sent to {email}. Our team will contact you shortly."}
    return {"answer": "Please provide a valid email address."}
