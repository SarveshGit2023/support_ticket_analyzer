import chainlit as cl
import asyncio
from rag import process_ticket, check_guardrails
from database import init_db, save_message, get_history, save_ticket
from config import WELCOME_MSG, THEME

init_db()

@cl.on_chat_start
async def start():
    cl.user_session.set("theme", THEME)
    cl.user_session.set("session_id", cl.user_session.get("id"))
    await cl.Message(content=WELCOME_MSG).send()

@cl.on_message
async def main(message: cl.Message):
    query = message.content
    session_id = cl.user_session.get("session_id")
    
    # Save user message to SQLite
    save_message(session_id, "user", query)

    # 1. Guardrail Check
    if not check_guardrails(query):
        warning = "🚨 **Security Alert:** Your input violates support guidelines or is unrecognizable as a ticket. Please rephrase."
        save_message(session_id, "assistant", warning)
        await cl.Message(content=warning).send()
        return

    # Simulate human processing time
    processing_msg = cl.Message(content="Analyzing ticket and historical data...")
    await processing_msg.send()
    await asyncio.sleep(1.5) # Artificial human delay

    # 2. Get History & Process
    history = get_history(session_id)
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]]) # Pass last 5 messages
    
    try:
        structured_data, docs = process_ticket(query, history_text)
        
        # Format for DB save
        ticket_dict = structured_data.dict()
        ticket_dict["ticket_text"] = query
        
        # 3. Assign ID and Save
        ticket_id = save_ticket(session_id, ticket_dict)

        # 4. Format Human-like Response
        ui_response = f"""
**Ticket Logged:** `{ticket_id}`
**Priority:** {structured_data.priority} | **Sentiment:** {structured_data.sentiment} | **Category:** {structured_data.issue_category}

**Suggested Resolution:**
{structured_data.suggested_response}

---
*Internal Notes: {structured_data.resolution_provided} (Est. {structured_data.resolution_time_est})*
"""     
        # FIX 1: Update the message content attribute directly
        processing_msg.content = ui_response
        await processing_msg.update()
        save_message(session_id, "assistant", ui_response)

    except Exception as e:
        # FIX 2: Apply the same syntax fix to the error handler
        processing_msg.content = f"🚨 **System Error:** {str(e)}"
        await processing_msg.update()