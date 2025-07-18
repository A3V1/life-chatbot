from config import llm
from langchain_core.prompts import PromptTemplate

def recognize_intent(query: str, chat_history: str) -> str:
    """
    Uses an LLM to classify the user's intent.
    """
    # Define intents
    intents = [
        "onboarding", # Continuing the guided flow
        "general_qa", # Asking a general question about insurance, policies, or the company
        "request_quote", # Explicitly asking for a price or quote
        "compare_policies", # Asking to compare features of different policies
        "request_agent", # Asking to speak to a human
        "random_talk" # Off-topic or conversational chatter
    ]

    # Create a prompt for the LLM
    prompt_template = PromptTemplate(
        template="""
        Based on the user's latest query and the chat history, classify the user's intent into one of the following categories:
        {intents}

        Chat History:
        {chat_history}

        User Query: "{query}"

        Rules:
        - If the query is a direct answer to a bot's question (like "Yes", "No", "35"), classify it as 'onboarding'.
        - If the user asks a question about a policy, a term, or the company, classify it as 'general_qa'.
        - If the user asks for a price or cost, classify it as 'request_quote'.
        - If the user asks to talk to a person, classify it as 'request_agent'.
        - For anything else, classify it as 'random_talk'.

        Intent:
        """,
        input_variables=["intents", "chat_history", "query"]
    )

    formatted_prompt = prompt_template.format(
        intents=", ".join(intents),
        chat_history=chat_history,
        query=query
    )

    try:
        response = llm.invoke(formatted_prompt)
        # Extract the intent from the response, ensuring it's one of the valid intents
        predicted_intent = response.content.strip().lower().replace(" ", "_")
        return predicted_intent if predicted_intent in intents else "onboarding"
    except Exception:
        # Default to 'onboarding' on error to keep the flow stable
        return "onboarding"
