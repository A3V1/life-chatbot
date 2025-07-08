import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pinecone_handler import upload_vectorstore

load_dotenv()

# --- LLM and RAG Setup ---
llm = ChatOpenAI(
    model="google/gemini-2.5-flash-lite-preview-06-17",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.7,
    max_tokens=150,  # Reduced token limit
    max_retries=3, # Retry on failure
)
vectorstore = upload_vectorstore("life-insurance")
retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

# --- Prompt for the Recommendation Phase ---
RECOMMENDATION_PROMPT = PromptTemplate(
    template="""You are a helpful insurance advisor. Based on the following context and user profile, recommend ONE best-fit policy.

Context:
{context}

User Profile:
{user_info}

User Query:
{query}

Respond ONLY in valid JSON like this:
{{
  "name": "Policy Name",
  "description": "Short reason why this policy is suitable for the user"
}}
""",
    input_variables=["user_info", "context", "query"],
)
