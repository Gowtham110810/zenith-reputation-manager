import os
import re
import sqlite3
import smtplib
import urllib.parse
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import central_core
import discovery_engine

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
SENDER_EMAIL = "zenith.ai.gowtham@gmail.com"
DAILY_EMAIL_LIMIT = 5

def get_smtp_password():
    pwd = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not pwd:
        try:
            import streamlit as st
            pwd = st.secrets.get("GMAIL_APP_PASSWORD", "")
        except Exception:
            pass
    return pwd.strip().replace(" ", "")

def get_today_sent_count():
    central_core.init_databases()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = sqlite3.connect(central_core.REPUTATION_DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM outreach_logs WHERE sent_date = ?", (today_str,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def is_already_contacted(target_email):
    central_core.init_databases()
    conn = sqlite3.connect(central_core.REPUTATION_DB)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM outreach_logs WHERE target_email = ?", (target_email.lower().strip(),))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def extract_emails(soup, html_text):
    emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html_text))
    return [e.lower() for e in emails if not e.lower().endswith((".png", ".jpg", ".css")) and "example.com" not in e]

def hunt_leads(category, city):
    central_core.init_databases()
    urls = discovery_engine.deep_discover_urls(category, city)
    leads = []
    
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code >= 400: continue
            soup = BeautifulSoup(resp.text, "html.parser")
            emails = extract_emails(soup, resp.text)
            if not emails: continue
            
            primary_email = emails[0]
            if is_already_contacted(primary_email): continue
            
            title = soup.find("title")
            b_name = title.get_text(strip=True).split("|")[0][:50] if title else "Local Business"
            
            pitch = (
                f"Hi {b_name} Team,\n\n"
                f"I was looking at your online presence in {city} and noticed you have several unanswered customer reviews. "
                f"Google's local SEO algorithm penalizes profiles that ignore customer feedback, which means you are actively losing Maps ranking and foot traffic to competitors.\n\n"
                f"I built an AI Reputation Manager that automatically writes keyword-optimized SEO replies to 5-star reviews and handles damage control for negative feedback instantly.\n\n"
                f"Would you be open to a 7-day free trial where I set this up for your business? Just reply 'YES' and I'll send over a live test.\n\n"
                f"Best regards,\nGowtham | Zenith AI\n{SENDER_EMAIL}"
            )
            
            leads.append({"business_name": b_name, "url": url, "emails": emails, "pitch": pitch})
        except Exception:
            continue
    return leads

def send_email(business_name, url, target_email, subject, body):
    central_core.init_databases()
    target_email = target_email.lower().strip()
    if get_today_sent_count() >= DAILY_EMAIL_LIMIT:
        return False, "Daily limit reached."
    if is_already_contacted(target_email):
        return False, "Already contacted."
    
    password = get_smtp_password()
    if not password: return False, "Missing Gmail App Password."
    
    msg = MIMEMultipart()
    msg["From"] = f"Gowtham | Zenith AI <{SENDER_EMAIL}>"
    msg["To"] = target_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.starttls()
        server.login(SENDER_EMAIL, password)
        server.send_message(msg)
        server.quit()
        
        now_utc = datetime.now(timezone.utc)
        conn = sqlite3.connect(central_core.REPUTATION_DB)
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO outreach_logs (business_name, url, target_email, subject, pitch, sent_date, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (business_name, url, target_email, subject, body, now_utc.strftime("%Y-%m-%d"), now_utc.isoformat()))
        conn.commit()
        conn.close()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)
