import json
import logging
from typing import Any, Dict
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from sqlconnect import (
    get_user_session,
    log_chat_message,
    update_user_context,
)
from handlers.onboarding import (
    handle_get_primary_need,
    # handle_get_insurance_goal,
    handle_collect_age,
    handle_collect_income,
    handle_collect_budget,
    handle_collect_term_length,
    handle_collect_coverage,
)
from handlers.recommendation import handle_recommendation_phase, _is_application_button
from handlers.closing import (
    handle_application,
    handle_contact_capture,
    handle_email_capture,
)
from handlers.general_qa import handle_general_questions
from utils import is_general_question

class ImprovedChatBot:
    def __init__(self, phone_number: str):
        session_data = get_user_session(phone_number)
        self.user_id = session_data["user_id"]
        self.context = session_data or {}
        self.memory = ConversationBufferMemory(
            chat_memory=ChatMessageHistory(),
            memory_key="chat_history",
            return_messages=True,
        )
        self._load_chat_history()

    def _load_chat_history(self):
        # Load chat history from context if available
        if "chat_history" in self.context and isinstance(self.context["chat_history"], list):
            for msg in self.context["chat_history"]:
                if msg.get("type") == "human":
                    self.memory.chat_memory.add_user_message(msg.get("data", {}).get("content", ""))
                elif msg.get("type") == "ai":
                    self.memory.chat_memory.add_ai_message(msg.get("data", {}).get("content", ""))

    def _update_context(self, updates: Dict[str, Any]):
        self.context.update(updates)
        # Also persist the chat history from memory into the context
        self.context["chat_history"] = [msg.dict() for msg in self.memory.buffer_as_messages]
        
        db_updates = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in self.context.items()}
        update_user_context(self.user_id, db_updates)

    def _validate_context_completeness(self) -> bool:
        """Ensure all required fields are collected before recommendations"""
        required_fields = ['primary_need', 'age', 'income', 'budget', 'term_length', 'coverage_required']
        return all(field in self.context for field in required_fields)

    def handle_message(self, query: str) -> Dict[str, Any]:
        current_state = self.context.get("context_state", "get_primary_need")
        
        # Define keywords that are specific to certain states and not general questions
        specific_keywords_map = {
            "recommendation_given_phase": ["compare", "details for", "apply for", "get more details"],
            # Add other states and their specific keywords here if needed
        }
        specific_keywords = specific_keywords_map.get(current_state, [])

        try:
            # Use the enhanced function to decide the routing
            logging.debug(f"Routing query: '{query}' in state: '{current_state}' with specific keywords: {specific_keywords}")
            is_general = is_general_question(query, specific_keywords=specific_keywords)
            logging.debug(f"is_general_question returned: {is_general}")

            if is_general:
                logging.debug("Routing to handle_general_questions.")
                response = handle_general_questions(self, query)
            else:
                logging.debug("Routing to _handle_state.")
                # Proceed with state-based handling
                response = self._handle_state(current_state, query)

            if query:
                log_chat_message(self.user_id, "user", query)
            if response and response.get("answer"):
                log_chat_message(self.user_id, "bot", response["answer"])
            
            # Manually update memory after handling
            self.memory.chat_memory.add_user_message(query)
            if response and response.get("answer"):
                self.memory.chat_memory.add_ai_message(response["answer"])

            return response
        except Exception as e:
            # Centralized error handling
            logging.error(f"Error in handle_message: {e}", exc_info=True)
            return {
                "answer": "I apologize, but I encountered an issue. Let's try to get back on track. What would you like to do?",
                "options": ["Start Over", "Get Policy Recommendations", "Speak to an Agent"]
            }

    def _handle_state(self, state: str, query: str) -> Dict[str, Any]:
        handlers = {
            "get_primary_need": handle_get_primary_need,
            # "get_insurance_goal": handle_get_insurance_goal,
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
