import os
import sqlite3
import requests
import central_core

def get_telegram_credentials():
    central_core.init_databases()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    try:
        import streamlit as st
        if not token:
            token = st.secrets.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not chat_id:
            chat_id = str(st.secrets.get("TELEGRAM_CHAT_ID", "")).strip()
    except Exception:
        pass

    conn = sqlite3.connect(central_core.REPUTATION_DB)
    cur = conn.cursor()
    if not token:
        cur.execute("SELECT value FROM settings WHERE key = 'telegram_token'")
        row = cur.fetchone()
        if row: token = row[0]
    if not chat_id:
        cur.execute("SELECT value FROM settings WHERE key = 'telegram_chat_id'")
        row = cur.fetchone()
        if row: chat_id = row[0]
    conn.close()
    return token, chat_id

def save_telegram_credentials(token, chat_id):
    central_core.init_databases()
    conn = sqlite3.connect(central_core.REPUTATION_DB)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('telegram_token', ?)", (token.strip(),))
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('telegram_chat_id', ?)", (str(chat_id).strip(),))
    conn.commit()
    conn.close()

def send_telegram_alert(message):
    token, chat_id = get_telegram_credentials()
    if not token or not chat_id:
        return False, "Telegram Token or Chat ID missing."
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        resp = requests.post(url, json=payload, timeout=10).json()
        if resp.get("ok"):
            return True, "Alert sent!"
        return False, resp.get("description", "Error")
    except Exception as e:
        return False, str(e)

def generate_ai_review_response(business_name, customer_name, rating, review_text, city):
    prompt = f"""
    You are an expert local SEO reputation manager for '{business_name}' located in '{city}'.
    A customer named '{customer_name}' left a {rating}-star review: "{review_text}"
    
    Write a professional review response:
    - If 4 or 5 stars: Express warm gratitude and naturally inject local SEO keywords (mentioning the city or specific service).
    - If 1, 2, or 3 stars: Write a polite, de-escalating apology, invite them to resolve the issue privately, and protect the brand's public image.
    
    Return ONLY the response text.
    """
    reply = central_core.call_gemini(prompt)
    if "Error:" in reply:
        if rating >= 4:
            return f"Thank you so much for the wonderful review, {customer_name}! We're thrilled you had a great experience with us here in {city}."
        else:
            return f"We are truly sorry to hear about your experience, {customer_name}. Please reach out to our management team directly so we can make things right."
    return reply
