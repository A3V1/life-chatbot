from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from cbot import ImprovedChatBot

app = FastAPI(
    title="Insurance Chatbot API",
    description="API for a stateful chatbot to guide users through selecting life insurance.",
    version="2.0.0",
)

# Allow CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Allow frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    phone_number: str = Field(..., description="The user's phone number, used as a unique identifier.")
    name: Optional[str] = Field(None, description="The user's name.")
    email: Optional[str] = Field(None, description="The user's email.")
    query: Optional[Any] = Field(None, description="The user's message (str) or form data (dict).")

class ChatResponse(BaseModel):
    answer: str
    options: Optional[List[str]] = None
    chat_history: Optional[List[dict]] = None
    input_type: Optional[str] = None
    slider_config: Optional[Dict[str, Any]] = None
    quote_data: Optional[Dict[str, Any]] = None

class QuotationRequest(BaseModel):
    phone_number: str
    dob: str
    gender: str
    nationality: str
    marital_status: str
    education: str
    gst_applicable: bool
    plan_option: str
    coverage_required: int
    premium_budget: Optional[int] = None
    policy_term: str
    premium_payment_term: str
    premium_frequency: str
    income_payout_frequency: str

# --- API Endpoints ---

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Handles all chat interactions.
    - If the query is empty/None, it's treated as the start of the conversation.
    - It initializes the bot, which loads context and history, and returns the appropriate message.
    """
    if not request.phone_number:
        raise HTTPException(status_code=400, detail="phone_number is required.")

    try:
        bot = ImprovedChatBot(
            phone_number=request.phone_number,
            name=request.name,
            email=request.email
        )
        
        # If it's the first message (no query), we also send back the history.
        if not request.query:
            history_from_context = bot.context.get("chat_history", [])
            
            # Check if resuming in the recommendation phase
            if bot.context.get("context_state") == "recommendation_given_phase" and bot.context.get("shown_recommendations"):
                last_recommendation_answer = "Based on your profile, here are two policies I recommend:" # A generic re-engagement message
                
                # Re-create the options based on the stored recommendations
                structured_policies = bot.context.get("shown_recommendations", [])
                options = [f"Apply for {item['name']}" for item in structured_policies] + ["Get More Details"]

                return {
                    "answer": last_recommendation_answer,
                    "options": options,
                    "chat_history": history_from_context,
                }

            # Get the initial welcome message from the bot
            response_data = bot.handle_message("")
            
            return {
                "answer": response_data.get("answer", "Welcome! How can I help?"),
                "options": response_data.get("options"),
                "chat_history": history_from_context,
            }

        # For subsequent messages, just handle the query.
        response_data = bot.handle_message(request.query)
        # Ensure chat_history is not sent on every turn to save bandwidth
        response_data["chat_history"] = []
        return response_data
    except Exception as e:
        print(f"An error occurred during chat: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")


@app.post("/api/update_user_and_get_quote")
def update_user_and_get_quote(request: QuotationRequest):
    """
    Updates user information and generates an insurance quote by calling the bot's method.
    """
    try:
        print("Received quote form data:")
        print(request.dict())

        bot = ImprovedChatBot(phone_number=request.phone_number)
        response = bot.update_profile_and_get_quote(request.dict())

        print("Quote response:", response)
        return response.get("quote_data")

    except Exception as e:
        print(f"An error occurred during quote generation: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during quote generation.")


@app.get("/")
def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"message": "Insurance Chatbot API is running."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
