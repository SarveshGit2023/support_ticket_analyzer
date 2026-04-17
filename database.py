import sqlite3
import json
import uuid
from datetime import datetime

DB_PATH = "support_sessions.db"

def init_db():
    # Thread-safe connection for concurrent access
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    # Session History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            session_id TEXT,
            timestamp DATETIME,
            role TEXT,
            content TEXT
        )
    """)
    
    # Structured Ticket Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_tickets (
            ticket_id TEXT PRIMARY KEY,
            session_id TEXT,
            issue_category TEXT,
            priority TEXT,
            sentiment TEXT,
            ticket_text TEXT,
            suggested_response TEXT,
            resolution_time_est TEXT,
            resolution_provided TEXT,
            created_at DATETIME
        )
    """)
    conn.commit()
    conn.close()

def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("INSERT INTO chat_history VALUES (?, ?, ?, ?)", 
                 (session_id, datetime.now(), role, content))
    conn.commit()
    conn.close()

def get_history(session_id):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.execute("SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    history = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in history]

def save_ticket(session_id, ticket_data):
    ticket_id = f"TCK-{uuid.uuid4().hex[:8].upper()}"
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    
    conn.execute("""
        INSERT INTO processed_tickets 
        (ticket_id, session_id, issue_category, priority, sentiment, ticket_text, suggested_response, resolution_time_est, resolution_provided, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id, session_id, ticket_data.get("issue_category"), ticket_data.get("priority"),
        ticket_data.get("sentiment"), ticket_data.get("ticket_text"), ticket_data.get("suggested_response"),
        ticket_data.get("resolution_time_est"), ticket_data.get("resolution_provided"), datetime.now()
    ))
    conn.commit()
    conn.close()
    return ticket_id