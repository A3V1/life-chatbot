import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pinecone_handler import upload_vectorstore

load_dotenv()

# --- LLM and RAG Setup ---
llm = ChatOpenAI(
    model="mistralai/mistral-small",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.7,
)
vectorstore = upload_vectorstore("life-insurance")
retriever = vectorstore.as_retriever()

# --- Prompt for the Recommendation Phase ---
RECOMMENDATION_PROMPT = PromptTemplate(
    template="""You are a helpful insurance assistant. Based on the user's profile and the provided policy data, recommend the top two most suitable policies. For each policy, provide a compelling one-line description.

User Info:
{user_info}

Relevant Policies:
{context}

User Query:
{query}

Based on your profile, here are two policies I recommend:

1.  **[Policy Name 1]**: [One-line description of policy 1].
2.  **[Policy Name 2]**: [One-line description of policy 2].

What would you like to do next?
""",
    input_variables=["user_info", "context", "query"],
)
