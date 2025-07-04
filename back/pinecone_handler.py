import os
import sys
import requests
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from sqlconnect import get_mysql_data
from decimal import Decimal
from datetime import datetime, date


def build_page_content(row):
    return f"Policy: {row[1]} from {row[2]}, with coverage up to ₹{row[5]} and premium of ₹{row[9]}."


def prepare_documents():
    mysql_data = get_mysql_data()
    documents = []

    for row in mysql_data:
        metadata = {
            "policy_id": row[0],
            "policy_name": row[1],
            "provider_name": row[2],
            "policy_type": row[3],
            "coverage_min": row[4],
            "coverage_amount": row[5],
            "policy_term_min": row[6],
            "policy_term_max": row[7],
            "premium_min": row[8],
            "premium": row[9],
            "entry_age_min": row[10],
            "entry_age_max": row[11],
            "claim_settlement_ratio": row[12],
            "riders": row[13],
            "exclusions": row[14],
            "tax_benefits": row[15],
            "payout_options": row[16],
            "benefits": row[17],
            "claim_process": row[18],
        }

        metadata = {k: v for k, v in metadata.items() if v is not None}

        for k, v in metadata.items():
            if isinstance(v, Decimal):
                metadata[k] = float(v)
            elif isinstance(v, (datetime, date)):
                metadata[k] = v.isoformat()
            elif not isinstance(v, (type(None), bool, dict, float, int, list, str)):
                metadata[k] = str(v)

        documents.append(Document(page_content=build_page_content(row), metadata=metadata))

    return documents


def upload_vectorstore(index_name="insurance-chatbot", namespace="default"):
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    try:
        embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    except requests.exceptions.ConnectionError:
        print("\n--- Network Connection Error ---")
        print("Failed to connect to Hugging Face to download the embedding model.")
        print("This is likely due to a network issue, a firewall blocking the connection, or a DNS problem.")
        print("Please check your internet connection and ensure 'huggingface.co' is accessible, then restart the application.")
        print("---------------------------------\n")
        sys.exit(1)
        
    documents = prepare_documents()

    # Optional: create the index if not present
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,  # match embedding size
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}  # adjust as needed
        )

    index = pc.Index(index_name)

    # Optional: clear old data
    try:
        index.delete(delete_all=True, namespace=namespace)
    except Exception as e:
        if "Namespace not found" not in str(e):
            raise

    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embedding,
        text_key="page_content",
        namespace=namespace
    )

    vectorstore.add_documents(documents)
    return vectorstore
