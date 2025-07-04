from pinecone_handler import upload_vectorstore
from dotenv import load_dotenv

def main():
    """
    This script loads data from MySQL, creates embeddings, and uploads them to Pinecone.
    """
    load_dotenv()
    print("Starting data embedding process...")
    upload_vectorstore("life-insurance")
    print("Data embedding process completed successfully.")

if __name__ == "__main__":
    main()
