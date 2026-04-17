import chromadb
import httpx
import json
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
# NEW: Import the robust output parser
from langchain_core.output_parsers import PydanticOutputParser
from config import *

client_http = httpx.Client(verify=False, timeout=httpx.Timeout(30.0))

llm = ChatOpenAI(
    model=LLM_MODEL,
    openai_api_key=GENAI_API_KEY,
    openai_api_base=GENAI_BASE_URL,
    http_client=client_http,
    temperature=0.1 # Dropped to 0.1 for even stricter formatting
)

class TicketResolution(BaseModel):
    issue_category: str = Field(description="Categorize the issue (e.g., Billing, Technical, Authentication)")
    priority: str = Field(description="Priority level: Low, Medium, High, Critical")
    sentiment: str = Field(description="User sentiment: Angry, Frustrated, Neutral, Happy")
    suggested_response: str = Field(description="A personalized, empathetic response resolving the issue")
    resolution_time_est: str = Field(description="Estimated time to resolve based on priority")
    resolution_provided: str = Field(description="Summary of the action taken or suggested")

# NEW: Initialize the parser
parser = PydanticOutputParser(pydantic_object=TicketResolution)

client_db = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client_db.get_or_create_collection(name=COLLECTION_NAME)

def get_embedding(text):
    response = client_http.post(
        f"{GENAI_BASE_URL}/v1/embeddings",
        headers={"Authorization": f"Bearer {GENAI_API_KEY}", "Content-Type": "application/json"},
        json={"model": EMBED_MODEL, "input": text}
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

def retrieve_docs(query):
    query_embedding = get_embedding(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=TOP_K)
    return results["documents"][0] if results["documents"] else []

def check_guardrails(query):
    response = llm.invoke(f"{GUARDRAIL_PROMPT}\n\nUser Input: {query}")
    return "UNSAFE" not in response.content.upper()

def process_ticket(query, history_context):
    docs = retrieve_docs(query)
    context = "\n\n".join(docs) if docs else "No historical resolutions found. Escalate to human agent."

    # NEW: Inject formatting instructions into the prompt
    prompt = f"""
    You are a tier-2 support engineer. Analyze the user's ticket and provide a structured resolution.
    
    Previous Conversation Context:
    {history_context}
    
    Historical Knowledge Base Context:
    {context}
    
    Current Ticket: {query}
    
    {parser.get_format_instructions()}
    """
    
    # NEW: Use the standard LLM invoke, then parse the text output
    raw_response = llm.invoke(prompt)
    structured_data = parser.invoke(raw_response)
    
    return structured_data, docs