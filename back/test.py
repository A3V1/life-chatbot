import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables from .env file
load_dotenv()

# Get Pinecone API key from environment variables
pinecone_api_key = os.getenv("PINECONE_API_KEY")

if pinecone_api_key:
    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)
    print("✅ Pinecone SDK working!")
else:
    print("❌ Pinecone API key not found. Make sure to set it in the .env file.")
