from sentence_transformers import SentenceTransformer
from .sqlconnect import get_mysql_data
import os

def load_embedding_model(model_name="all-MiniLM-L6-v2"):
    """Loads a sentence transformer model."""
    return SentenceTransformer(model_name)

def get_embeddings(model, texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a list of texts."""
    return model.encode(texts, convert_to_tensor=False).tolist()

def chunk_text(text, max_chars=500):
    """Chunks text into smaller pieces."""
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
