import os
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from sqlconnect import get_mysql_data
from decimal import Decimal
from datetime import datetime, date


def build_page_content(row):
    return f"""Policy Name: {row[2]}
Policy Type: {row[3]}
Coverage Amount: ₹{row[5]}
Annual Premium: ₹{row[4]}
Sum Assured: ₹{row[6]}

Eligibility: {row[19]}
Entry Age: {row[12]}–{row[13]} years
Policy Term: {row[14]}–{row[15]} years
Renewability: {row[16]}

Claim Process: {row[17]}
Maturity Benefits: {row[10]}
Return on Maturity: {row[11]}
Waiting Period: {row[9]}

Tax Benefits: {row[18]}
"""


def prepare_documents():
    mysql_data = get_mysql_data()
    documents = []

    for row in mysql_data:
        metadata = {
            "id": row[0],
            "insurer_name": row[1],
            "policy_name": row[2],
            "policy_type": row[3],
            "premium": row[4],
            "coverage_amount": row[5],
            "sum_assured": row[6],
            "co_payment": row[7],
            "network_hospitals": row[8],
            "waiting_period": row[9],
            "maturity_benefits": row[10],
            "return_on_maturity": row[11],
            "entry_age_min": row[12],
            "entry_age_max": row[13],
            "policy_term_min": row[14],
            "policy_term_max": row[15],
            "renewability": row[16],
            "claim_process": row[17],
            "tax_benefits": row[18],
            "eligibility": row[19],
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
    embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
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
