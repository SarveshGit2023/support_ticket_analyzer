import pandas as pd
from tqdm import tqdm
import httpx
import chromadb
import os
from config import (
    GENAI_API_KEY, GENAI_BASE_URL, EMBED_MODEL,
    PERSIST_DIR, COLLECTION_NAME
)

os.makedirs(PERSIST_DIR, exist_ok=True)

client_http = httpx.Client(verify=False, timeout=httpx.Timeout(30.0))

def get_embedding(text):
    response = client_http.post(
        f"{GENAI_BASE_URL}/v1/embeddings",
        headers={
            "Authorization": f"Bearer {GENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": EMBED_MODEL,
            "input": text
        }
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

try:
    df = pd.read_csv("data/support_tickets_v2.csv")
    df.fillna("No data provided", inplace=True)
except FileNotFoundError:
    print("❌ Critical Error: 'data/support_tickets_v2.csv' not found. Ensure the data directory exists.")
    exit(1)

def build_doc(row):
    return f"""
Issue: {row.get('title', '')}
Description: {row.get('description', '')}
Resolution: {row.get('resolution', '')}
""".strip()

docs = df.apply(build_doc, axis=1).tolist()
docs = [d for d in docs if d.strip()]

print(f"🚀 Starting ingestion for {len(docs)} documents into '{COLLECTION_NAME}'...")

for i, doc in tqdm(enumerate(docs), total=len(docs)):
    try:
        emb = get_embedding(doc)
        collection.add(
            documents=[doc],
            embeddings=[emb],
            ids=[str(i)]
        )
    except Exception as e:
        print(f"⚠️ Failed to embed/store document index {i}. Error: {str(e)}")

print(f"\n✅ Ingestion complete. Vector store persisted at '{PERSIST_DIR}'")