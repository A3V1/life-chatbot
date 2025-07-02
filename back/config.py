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
    template="""You are an expert life insurance advisor. The user has provided their complete profile. Your task is to recommend 2-3 specific insurance plans that fit their profile and budget.

User Profile (Context):
{context}

Conversation History:
{chat_history}

Retrieved Policy Information (for reference):
{retrieved_docs}

IMPORTANT INSTRUCTIONS:
1. **Budget Validation**: User's monthly budget is {monthly_budget}. Annual budget is {annual_budget}. ONLY recommend policies with premiums within this budget.
2. **Recommend 2-3 Policies**: Provide specific policy names with realistic premiums that fit the budget.
3. **Be Specific**: Include exact coverage amounts, premium amounts, and key features.
4. **Format**: Use clear headings and bullet points for easy reading.
5. for each policy advised only give 1-2 sentences per policy.
User's latest message: "{query}"

Provide realistic policy recommendations that actually fit their budget:""",
    input_variables=["context", "chat_history", "retrieved_docs", "query", "monthly_budget", "annual_budget"],
)
