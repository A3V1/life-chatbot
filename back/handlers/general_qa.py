import json
import logging
from typing import Any, Dict
from langchain_core.prompts import PromptTemplate
from config import llm, retriever

def handle_general_questions(bot, query: str) -> Dict[str, Any]:
    """
    Handles open-ended general questions, provides a concise answer, and prompts to continue.
    """
    # Store the state before the diversion
    state_before_diversion = bot.context.get("context_state")
    bot._update_context({"state_before_diversion": state_before_diversion})
    # 1. Retrieve relevant documents
    docs = retriever.invoke(query)
    context_str = "\n\n".join([doc.page_content for doc in docs])

    # 2. Extract user profile and chat history
    user_profile = json.dumps({
        k: v for k, v in bot.context.items() 
        if k not in ["chat_history", "state_history", "retrieved_docs"] and v is not None
    }, default=str)
    chat_history = "\n".join([f"{msg.type}: {msg.content}" for msg in bot.memory.buffer_as_messages])

    # 3. Define the comprehensive prompt template
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

    # 4. Manually format the prompt with all the information
    formatted_prompt = prompt_template.format(
        context=context_str,
        question=query,
        user_profile=user_profile,
        chat_history=chat_history
    )

    # 5. Invoke the LLM directly
    try:
        llm_response = llm.invoke(formatted_prompt)
        answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
    except Exception as e:
        # Fallback in case of LLM error
        logging.error(f"Error in handle_general_questions during LLM call: {e}", exc_info=True)
        answer = "I'm having a bit of trouble processing that. Could you try rephrasing your question?"

    # After answering, prompt the user to get back to the flow
    previous_state_handler = bot.get_handler_for_state(state_before_diversion)
    if previous_state_handler:
        # Get the question for the previous state
        reprompt_message = previous_state_handler(bot, "").get("answer", "Shall we continue?")
        answer += f"\n\nNow, back to where we were. {reprompt_message}"

    return {
        "answer": answer,
        "options": bot.get_handler_for_state(state_before_diversion)(bot, "").get("options", [])
    }
