import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from back.cbot import ImprovedChatBot
from back.sqlconnect import get_or_create_user


def run_cli_chat():
    """
    Runs an interactive command-line chat session with the Life Insurance Chatbot.
    """
    # 1. Get phone number from user
    phone_number = input("Enter your 10-digit phone number to start: ")
    while not (phone_number.isdigit() and len(phone_number) == 10):
        phone_number = input("Please enter a valid 10-digit phone number: ")

    # 2. Instantiate the ChatBot
    bot = ImprovedChatBot(phone_number=phone_number)
    print(f"Chat session started for {phone_number}. Type 'exit' or 'quit' to end.")
    print("-" * 30)

    # 3. Start the interactive loop, sending an empty query first to get the welcome message
    query = ""
    while True:
        try:
            response = bot.handle_message(query)
            print(f"Bot: {response.get('answer')}")

            # If the bot provides options, display them.
            if response.get('options'):
                for i, option in enumerate(response['options'], 1):
                    print(f"  {i}. {option}")
            
            print("-" * 30)

            query = input("You: ")
            if query.lower() in ["exit", "quit"]:
                print("Bot: Goodbye!")
                break

        except (KeyboardInterrupt, EOFError):
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break


if __name__ == "__main__":
    run_cli_chat()
