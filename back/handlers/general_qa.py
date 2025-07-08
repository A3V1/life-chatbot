import json
import logging
from typing import Any, Dict
from langchain_core.prompts import PromptTemplate
from config import llm, retriever

def route_general_question(bot, query: str, intent: str = "general_qa") -> Dict[str, Any]:
    """
    Routes the user's general question to the appropriate handler based on intent.
    """
    state_before_diversion = bot.context.get("context_state")
    bot._update_context({  
        "state_before_diversion": state_before_diversion,
        "last_user_query": query,
        "user_intent": intent,
        "diversion_count": bot.context.get("diversion_count", 0) + 1
    })

    if intent == "general_qa":
        response = handle_general_questions(bot, query)
    else:
        # In the future, other intents can be routed here.
        # For now, we'll just use the general handler.
        response = handle_general_questions(bot, query)

    # Dynamic "nudge back" logic
    previous_state_handler = bot.get_handler_for_state(state_before_diversion)
    if previous_state_handler:
        resumed = previous_state_handler(bot, "")
        reprompt_message = resumed.get("answer", "Shall we continue?")
        options = resumed.get("options", [])
        
        # Add a polite redirection message
        response["answer"] += f"\n\nI hope that helps. {reprompt_message}"
        response["options"] = options
    else:
        logging.warning(f"No handler found for state '{state_before_diversion}'")
        response["options"] = ["Start Over", "Get Policy Recommendations"]

    return response


def handle_general_questions(bot, query: str) -> Dict[str, Any]:
    """
    Handles a general question using a RAG-based approach.
    """
    # 1. Retrieve relevant documents
    docs = retriever.invoke(query)
    context_str = "\n\n".join([doc.page_content for doc in docs])

    # 2. Extract user profile and chat history
    user_profile = json.dumps({
        k: v for k, v in bot.context.items() 
        if k not in ["chat_history", "state_history", "retrieved_docs"] and v is not None
    }, default=str)
    chat_history = "\n".join([f"{msg.type}: {msg.content}" for msg in bot.memory.buffer_as_messages])

    # 3. Define the prompt
    prompt_template = PromptTemplate(
        template="""You are a helpful and knowledgeable insurance assistant. Your goal is to provide accurate and context-aware answers.
**IMPORTANT**: Keep your answer concise and to the point, ideally under 40 words.

Here is the user's profile:
{user_profile}

Here is the recent conversation history:
{chat_history}

Based on the retrieved documents below and the user's profile/history, answer the user's question.

Retrieved Documents (Context):
{context}

User Question:
{question}

---
Follow these instructions carefully:
1.  Analyze the user's question in the context of their profile and chat history.
2.  If the user asks a subjective question (e.g., "which is better for me?", "what should I choose?"), **do not give a direct recommendation**. Instead:
    a. Acknowledge that you cannot make the decision for them.
    b. Use the retrieved documents to objectively highlight the key differences between the options.
    c. Mention the personal factors the user should consider (e.g., age, budget, financial goals, risk tolerance) based on their profile.
    d. Empower the user to make an informed decision.
3.  If the answer is in the retrieved documents, provide a clear and concise answer.
4.  If the answer is not in the documents and it's not a subjective question, state that you don't have the specific information to answer.

Answer:
""",
        input_variables=["context", "question", "user_profile", "chat_history"],
    )

    # 4. Format the prompt
    formatted_prompt = prompt_template.format(
        context=context_str,
        question=query,
        user_profile=user_profile,
        chat_history=chat_history
    )

    # 5. LLM call
    try:
        llm_response = llm.invoke(formatted_prompt)
        answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
    except Exception as e:
        logging.error(f"Error in handle_general_questions during LLM call: {e}", exc_info=True)
        answer = "I'm having a bit of trouble processing that. Could you try rephrasing your question?"

    return {"answer": answer}

def handle_random_query(bot, query: str) -> Dict[str, Any]:
    """Handles any query that doesn't fit into the structured flow."""
    chat_history = "\n".join([f"{msg.type}: {msg.content}" for msg in bot.memory.buffer_as_messages])
    
    prompt = f"""You are a friendly and helpful assistant. The user has asked something that is not related to the current conversation. 
    
    Recent conversation:
    {chat_history}
    
    User's query: "{query}"
    
    Please provide a short, conversational response to the user's query.
    """
    
    try:
        llm_response = llm.invoke(prompt)
        answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
    except Exception as e:
        logging.error(f"Error in handle_random_query during LLM call: {e}", exc_info=True)
        answer = "I'm not sure how to respond to that. Could you try asking something else?"
        
    return {"answer": answer}
