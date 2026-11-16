import os
import sqlite3
from google import genai

REPUTATION_DB = "reputation_manager.db"


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
    return key.strip()


def init_databases():
    """Initializes SQLite tables for reviews, settings, and outreach."""
    conn = sqlite3.connect(REPUTATION_DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            customer_name TEXT,
            rating INTEGER,
            review_text TEXT,
            ai_reply TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS outreach_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            url TEXT,
            target_email TEXT UNIQUE,
            subject TEXT,
            pitch TEXT,
            sent_date TEXT,
            sent_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def call_gemini(prompt: str) -> str:
    api_key = get_api_key()
    if not api_key:
        return "Error: GEMINI_API_KEY not configured."
    try:
        client = genai.Client(api_key=api_key)
        preferred = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        for model_name in preferred:
            try:
                resp = client.models.generate_content(model=model_name, contents=prompt)
                if resp and resp.text:
                    return resp.text.strip()
            except Exception:
                continue
        return "Error: No compatible Gemini model responded."
    except Exception as e:
        return f"System Error: {str(e)}"
