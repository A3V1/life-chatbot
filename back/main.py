from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
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
    query: Optional[str] = Field(None, description="The user's message to the chatbot. Send an empty string for the first message.")

class ChatResponse(BaseModel):
    answer: str
    options: Optional[List[str]] = None
    chat_history: Optional[List[dict]] = None

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
        bot = ImprovedChatBot(phone_number=request.phone_number)
        
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
        return {
            "answer": response_data.get("answer", "Sorry, something went wrong."),
            "options": response_data.get("options"),
            "chat_history": [], # No need to send history on every turn
        }
    except Exception as e:
        print(f"An error occurred during chat: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")


@app.get("/")
def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"message": "Insurance Chatbot API is running."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
