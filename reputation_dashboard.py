import sqlite3
import pandas as pd
import streamlit as st
import central_core
import reputation_engine
import reputation_lead_hunter

st.set_page_config(page_title="Zenith AI Reputation Manager", page_icon="⭐", layout="wide")
central_core.init_databases()

if "rep_leads" not in st.session_state:
    st.session_state.rep_leads = []

# --- THE LOCAL SEO INTELLIGENCE QUEUE ---
if "smart_queue_rep" not in st.session_state:
    st.session_state.smart_queue_rep = [
        ("Dental Clinics", "Hyderabad", "High lifetime value patients; clinics desperately need 5-star local SEO."),
        ("Fine Dining Restaurants", "Mumbai", "High competition; one bad review costs thousands in reservations."),
        ("Dermatologists", "Bengaluru", "Highly searched on Maps; extreme reliance on patient reviews."),
        ("Boutique Gyms", "Pune", "Membership-driven; local map packs dominate acquisition."),
        ("Luxury Salons", "New Delhi", "Aesthetic-focused; reviews dictate foot traffic."),
        ("Chiropractors", "Chennai", "Trust-based service; local SEO is their primary marketing channel."),
        ("Veterinary Clinics", "Hyderabad", "Pet owners strictly filter by 4.5+ stars on Google Maps."),
        ("Med Spas", "Mumbai", "High-margin aesthetics; negative reviews destroy trust instantly."),
        ("Boutique Cafes", "Bengaluru", "Massive reliance on Google Maps "near me" searches."),
        ("Real Estate Agencies", "Gurgaon", "High-ticket transactions requiring flawless online reputation.")
    ]

st.title("⭐ AI Reputation & Local SEO Review Manager")
st.caption("Rank 3 B2B SaaS: Automated SEO Review Responses + Telegram Alerts + Local Business Lead Hunter")

tab1, tab2, tab3 = st.tabs([
    "💬 Review Reply & SEO Generator",
    "📲 Telegram Bot Setup",
    "🎯 Local SEO Lead Hunter (5/Day Cap)"
])

with tab1:
    st.subheader("Generate Keyword-Optimized AI Responses for Customer Reviews")
    with st.form("review_form"):
        b_name = st.text_input("Business Name", value="Apex Dental Clinic")
        city = st.text_input("City", value="Hyderabad")
        c_name = st.text_input("Customer Name", value="Rahul Sharma")
        rating = st.slider("Star Rating", 1, 5, 5)
        review_text = st.text_area("Customer Review Text", value="Amazing experience! The staff was super polite and the root canal was completely painless.")
        gen_btn = st.form_submit_button("✨ Generate SEO Reply & Notify Telegram")

    if gen_btn:
        with st.spinner("Drafting keyword-rich SEO response..."):
            reply = reputation_engine.generate_ai_review_response(b_name, c_name, rating, review_text, city)
            st.success("Generated Response:")
            st.info(reply)
            
            alert_text = (
                f"⭐ <b>New {rating}-Star Review for {b_name}!</b>\n\n"
                f"<b>Customer:</b> {c_name}\n"
                f"<b>Review:</b> \"{review_text}\"\n\n"
                f"🤖 <b>AI SEO Draft:</b>\n<i>{reply}</i>"
            )
            ok, msg = reputation_engine.send_telegram_alert(alert_text)
            if ok:
                st.toast("📲 Sent draft to your Telegram!")
            else:
                st.warning(f"Telegram notice: {msg}")

with tab2:
    st.subheader("Connect Telegram Bot")
    saved_token, saved_chat_id = reputation_engine.get_telegram_credentials()
    token_in = st.text_input("Bot Token", value=saved_token, type="password")
    chat_in = st.text_input("Chat ID", value=saved_chat_id)
    if st.button("💾 Save & Test"):
        reputation_engine.save_telegram_credentials(token_in, chat_in)
        ok, msg = reputation_engine.send_telegram_alert("⭐ Zenith Reputation Manager Connected!")
        if ok: st.success("Test alert sent!")
        else: st.error(msg)

with tab3:
    st.subheader("Smart Local Business Discovery (zenith.ai.gowtham@gmail.com)")
    sent_today = reputation_lead_hunter.get_today_sent_count()
    remaining = max(0, reputation_lead_hunter.DAILY_EMAIL_LIMIT - sent_today)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Daily Limit", "5 Emails/Day")
    m2.metric("Sent Today", sent_today)
    m3.metric("Remaining", remaining)

    st.markdown("### 🧠 Smart Auto-Pilot Engine")
    st.caption("Systematically targets high-ticket local businesses that rely heavily on Google Maps ranking.")

    if st.button("🚀 1-Click Smart Discover", use_container_width=True):
        if not st.session_state.smart_queue_rep:
            st.warning("You have exhausted the Top 10 Local Markets! Refresh the page to reset the queue or use Manual Override.")
        else:
            niche, city, logic = st.session_state.smart_queue_rep.pop(0)
            st.info(f"**🧠 Intelligence Engine Active:** Targeting '{niche}' in '{city}'. \n*Reasoning:* {logic}")

            with st.spinner(f"Scanning for '{niche}' in '{city}' with unanswered reviews..."):
                st.session_state.rep_leads = reputation_lead_hunter.hunt_leads(niche, city)

            if not st.session_state.rep_leads:
                st.warning(f"Scan complete for '{niche}' in '{city}', but no uncontacted public emails were found. Click 'Smart Discover' again to move to the next market.")
            else:
                st.success(f"Successfully found {len(st.session_state.rep_leads)} local lead(s) for '{niche}' in '{city}'!")

    with st.expander("Manual Override (Type your own niche)"):
        with st.form("hunt_form"):
            col1, col2 = st.columns(2)
            manual_niche = col1.text_input("Business Category", value="Pediatricians")
            manual_city = col2.text_input("Target City", value="Chennai")
            hunt_btn = st.form_submit_button("🔍 Find Local Leads")

        if hunt_btn:
            with st.spinner("Scanning local businesses..."):
                st.session_state.rep_leads = reputation_lead_hunter.hunt_leads(manual_niche, manual_city)
            if not st.session_state.rep_leads:
                st.warning("No uncontacted leads found. Try a different city.")

    leads = st.session_state.rep_leads
    if leads:
        st.divider()
        if remaining > 0:
            if st.button(f"⚡ Auto-Send Top {min(len(leads), remaining)} Pitches Now"):
                for idx, lead in enumerate(leads):
                    if reputation_lead_hunter.get_today_sent_count() >= reputation_lead_hunter.DAILY_EMAIL_LIMIT:
                        break
                    target_email = lead["emails"][0]
                    if reputation_lead_hunter.is_already_contacted(target_email):
                        continue
                    subject = f"Boost your Google Maps Ranking & Reviews for {lead['business_name']}"
                    pitch_text = st.session_state.get(f"rpitch_{idx}", lead["pitch"])
                    ok, msg = reputation_lead_hunter.send_email(
                        lead["business_name"], lead["url"], target_email, subject, pitch_text
                    )
                    if ok:
                        st.toast(f"✅ Sent to {target_email}")
                    else:
                        st.error(f"❌ {target_email}: {msg}")
                st.rerun()
        else:
            st.warning("🔒 Daily limit of 5 automated emails reached. Lock will release tomorrow.")

        for idx, lead in enumerate(leads):
            target_email = lead["emails"][0]
            already_sent = reputation_lead_hunter.is_already_contacted(target_email)
            badge = "✅ SENT" if already_sent else "🟢 READY"
            with st.expander(f"{badge} | #{idx+1}: {lead['business_name']} ({lead['url']})", expanded=(idx < 5 and not already_sent)):
                st.write(f"**Email:** `{target_email}`")
                pitch = st.text_area("Pitch:", value=lead["pitch"], height=150, key=f"rpitch_{idx}")
                if st.button("🚀 Send Email", key=f"rsend_{idx}", disabled=(already_sent or remaining == 0)):
                    with st.spinner("Sending..."):
                        subject = f"Boost your Google Maps Ranking & Reviews for {lead['business_name']}"
                        ok, msg = reputation_lead_hunter.send_email(lead["business_name"], lead["url"], target_email, subject, pitch)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
