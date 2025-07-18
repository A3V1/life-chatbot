import json
import logging
from typing import Any, Dict
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from sqlconnect import (
    get_user_session,
    log_chat_message,
    update_user_context,
)
from handlers.onboarding import (
    handle_existing_policy,
    handle_employment_status,
    handle_annual_income,
)
from handlers.recommendation import (
    handle_recommendation_phase,
)
from handlers.closing import (
    handle_application,
    handle_contact_capture,
    handle_email_capture,
)
from handlers.general_qa import route_general_question, handle_random_query, handle_general_questions
from utils import is_general_question

from handlers.quotation import QuotationHandler, handle_generate_premium_quotation
class ImprovedChatBot:
    def __init__(self, phone_number: str, name: str = None, email: str = None):
        session_data = get_user_session(phone_number, name, email)
        self.user_id = session_data["user_id"]
        self.context = session_data or {}
        self.memory = ConversationBufferWindowMemory(
            chat_memory=ChatMessageHistory(),
            memory_key="chat_history",
            return_messages=True,
            k=5  # Keep the last 5 interactions
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
        
        # Persist only the changes to the database
        db_updates = updates.copy()

        # Add chat history to the updates if it has changed
        self.context["chat_history"] = [msg.dict() for msg in self.memory.buffer_as_messages]
        db_updates["chat_history"] = self.context["chat_history"]

        # --- CONTEXT TO DB MAPPING ---
        # Map the application key 'policy_term' to the database column 'term_length'
        if 'policy_term' in db_updates:
            db_updates['term_length'] = db_updates.pop('policy_term')
        # --- END MAPPING ---

        update_user_context(self.user_id, db_updates)

    def _validate_context_completeness(self) -> bool:
        """Ensure all required fields are collected before recommendations"""
        # Onboarding validation
        onboarding_fields = ['existing_policy', 'employment_status', 'annual_income']
        if self.context.get("context_state") in ["recommendation_phase"]:
            return all(field in self.context for field in onboarding_fields)

        # Full validation before quote generation
        full_fields = onboarding_fields + [
            'dob', 'gender', 'nationality', 'marital_status', 
            'education', 'gst_applicable'
        ]
        return all(field in self.context for field in full_fields)

    def handle_message(self, query: Any) -> Dict[str, Any]:
        # --- Existing text-based message handling ---
        current_state = self.context.get("context_state", "existing_policy")
        
        specific_keywords_map = {
            "recommendation_given_phase": ["compare", "details for", "apply for", "get more details"],
        }
        specific_keywords = specific_keywords_map.get(current_state, [])

        try:
            is_general = is_general_question(query, specific_keywords=specific_keywords)
            logging.debug(f"Routing query: '{query}' in state: '{current_state}'. Is general: {is_general}")

            if is_general:
                response = route_general_question(self, query)
            else:
                response = self._handle_state(current_state, query)
                
                if not response:
                    new_state = self.context.get("context_state")
                    if new_state != current_state:
                        logging.debug(f"Handler returned empty, transitioning to new state: {new_state}")
                        response = self._handle_state(new_state, "")
                    else:
                        # If the state hasn't changed and the handler returned nothing,
                        # it's a random query.
                        logging.debug(f"No specific handler for query in state '{current_state}'. Treating as random query.")
                        response = handle_random_query(self, query)

            if query:
                # If the query is a dictionary (form submission), convert it to a string for logging
                if isinstance(query, dict):
                    log_message = json.dumps(query)
                    self.memory.chat_memory.add_user_message(log_message)
                else:
                    log_message = query
                    self.memory.chat_memory.add_user_message(query)
                
                log_chat_message(self.user_id, "user", log_message)

            if response and response.get("answer"):
                log_chat_message(self.user_id, "bot", response["answer"])
                self.memory.chat_memory.add_ai_message(response["answer"])

            return response
        except Exception as e:
            # Centralized error handling
            logging.error(f"Error in handle_message: {e}", exc_info=True)
            return {
                "answer": "I apologize, but I encountered an issue. Let's try to get back on track. What would you like to do?",
                "options": ["Start Over", "Get Policy Recommendations", "Speak to an Agent"]
            }

    def _handle_state(self, state: str, query: Any) -> Dict[str, Any]:
        handlers = {
            # Onboarding
            "existing_policy": handle_existing_policy,
            "collect_employment_status": handle_employment_status,
            "collect_annual_income": handle_annual_income,
            
            # Recommendation
            "recommendation_phase": handle_recommendation_phase,
            "recommendation_given_phase": handle_recommendation_phase,

            "generate_premium_quotation": handle_generate_premium_quotation,

            # Closing
            "application": handle_application,
            "contact_capture": handle_contact_capture,
            "email_capture": handle_email_capture,
        }
        handler = handlers.get(state, handle_existing_policy)
        return handler(self, query)

    def get_handler_for_state(self, state: str):
        """Returns the handler function for a given state."""
        handlers = {
            "existing_policy": handle_existing_policy,
            "collect_employment_status": handle_employment_status,
            "collect_annual_income": handle_annual_income,
            "recommendation_phase": handle_recommendation_phase,
            "recommendation_given_phase": handle_recommendation_phase,
            "generate_premium_quotation": handle_generate_premium_quotation,
            "application": handle_application,
            "contact_capture": handle_contact_capture,
            "email_capture": handle_email_capture,
            "quote_displayed": handle_general_questions,}
        return handlers.get(state)

    def update_profile_and_get_quote(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates user profile from form, generates a quote, and saves it.
        """
        # 1. Update user_info and user_context
        user_info_keys = [
            "dob", "gender", "nationality", "marital_status",
            "education", "gst_applicable", "employment_status", "annual_income", "existing_policy"
        ]
        
        user_context_keys = ["plan_option","coverage_required", "premium_budget", "policy_term", "premium_payment_term", "income_payout_frequency","premium_frequency"]
        user_info_data = {k: form_data[k] for k in user_info_keys if k in form_data}
        user_context_data = {k: form_data[k] for k in user_context_keys if k not in user_info_keys}

        if user_info_data:
            from sqlconnect import update_user_info
            update_user_info(self.user_id, user_info_data)
        
        if user_context_data:
            self._update_context(user_context_data)

        # 2. Reload context and apply form data
        self.context = get_user_session(self.context["phone_number"])
        self.context.update(user_context_data)

        # 3. Generate quote
        from handlers.quotation import QuotationHandler
        from sqlconnect import get_mysql_connection, save_quotation_details
        db_conn = get_mysql_connection()
        quotation_handler = QuotationHandler(self, self.user_id, self.context)
        response = quotation_handler.handle()
        db_conn.close()

        # 4. Save the generated quote to the new table
        if response.get("quote_data"):
            # The quote_data might be nested, let's ensure we get the flat dictionary
            flat_quote_data = response["quote_data"].get("quote_data", response["quote_data"])
            
            # Add form data that might not be in the quote response but is in the table
            for key in form_data:
                if key not in flat_quote_data:
                    flat_quote_data[key] = form_data[key]
            
            save_quotation_details(self.user_id, flat_quote_data)
            
            # Also update the user_context with the quote details
            self._update_context(flat_quote_data)

        return response
