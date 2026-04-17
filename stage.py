# =========================
# 📁 app.py (Chainlit)
# =========================
import chainlit as cl
from rag import retrieve_docs, generate_response


@cl.on_chat_start
async def start():
    await cl.Message(content="👋 Welcome to AI Support Assistant. Ask your query.").send()


@cl.on_message
async def main(message: cl.Message):
    query = message.content

    docs = retrieve_docs(query)
    answer = generate_response(query, docs)

    sources = "\n".join([f"- {d}" for d in docs])

    final = f"""
{answer}

---
📚 Sources:
{sources}
"""

    await cl.Message(content=final).send()


# =========================
# 📁 requirements.txt
# =========================
chainlit
chromadb
sentence-transformers
langchain-openai
python-dotenv
httpx


# =========================
# ▶️ RUN STEPS
# =========================
# 1. pip install -r requirements.txt
# 2. python ingest.py
# 3. chainlit run app.py
