import json
from typing import Any, Dict
from langchain.memory import ConversationBufferMemory
from sqlconnect import (
    get_chat_history,
    get_or_create_user,
    get_user_context,
    log_chat_message,
    update_user_context,
)
from handlers.onboarding import (
    handle_get_primary_need,
    handle_get_insurance_goal,
    handle_collect_age,
    handle_collect_income,
    handle_collect_budget,
    handle_collect_term_length,
    handle_collect_coverage,
)
from handlers.recommendation import handle_recommendation_phase
from handlers.closing import (
    handle_application,
    handle_contact_capture,
    handle_email_capture,
)

class ImprovedChatBot:
    def __init__(self, phone_number: str):
        user_data = get_or_create_user(phone_number=phone_number)
        self.user_id = user_data["user_id"]
        self.context = get_user_context(self.user_id) or {}
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self._load_chat_history()

    def _load_chat_history(self):
        chat_history = get_chat_history(self.user_id)
        for msg_type, msg in chat_history:
            (self.memory.chat_memory.add_user_message if msg_type == "user" else self.memory.chat_memory.add_ai_message)(msg)

    def _update_context(self, updates: Dict[str, Any]):
        self.context.update(updates)
        db_updates = {k: (json.dumps(v) if isinstance(v, list) else v) for k, v in updates.items()}
        update_user_context(self.user_id, db_updates)

    def _validate_context_completeness(self) -> bool:
        """Ensure all required fields are collected before recommendations"""
        required_fields = ['primary_need', 'insurance_goal', 'age', 'income', 'budget', 'term_length', 'coverage_required']
        return all(field in self.context for field in required_fields)

    def handle_message(self, query: str) -> Dict[str, Any]:
        current_state = self.context.get("context_state", "get_primary_need")
        
        # Handle general queries that can occur at any state
        if query.lower() in ["compare policies", "get more details", "show different options"]:
            return handle_recommendation_phase(self, query)

        try:
            response = self._handle_state(current_state, query)
            
            if query: log_chat_message(self.user_id, "user", query)
            if response.get("answer"): log_chat_message(self.user_id, "bot", response["answer"])
                
            return response
        except Exception as e:
            # Error handling with fallback response
            return {
                "answer": "I apologize, but I encountered an issue. Let me help you continue. What would you like to know about insurance policies?",
                "options": ["Start Over", "Get Policy Recommendations", "Speak to Agent"]
            }

    def _handle_state(self, state: str, query: str) -> Dict[str, Any]:
        handlers = {
            "get_primary_need": handle_get_primary_need,
            "get_insurance_goal": handle_get_insurance_goal,
            "collect_age": handle_collect_age,
            "collect_income": handle_collect_income,
            "collect_budget": handle_collect_budget,
            "collect_term_length": handle_collect_term_length,
            "collect_coverage": handle_collect_coverage,
            "recommendation_given_phase": handle_recommendation_phase,
            "application": handle_application,
            "contact_capture": handle_contact_capture,
            "email_capture": handle_email_capture,
        }
        handler = handlers.get(state, handle_get_primary_need)
        return handler(self, query)
