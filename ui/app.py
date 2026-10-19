import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from app.db import get_conn, init_db
from app.agents.classifier import Classification
from app.pipeline import process, handle_ticket

init_db()
st.set_page_config(page_title="SupportPilot", layout="wide")
st.title("SupportPilot")

def resolve(ticket_id, order_id, approve, reply):
    with get_conn() as conn:
        conn.execute("UPDATE tickets SET status=?, agent_reply=? WHERE id=?",
                     ("resolved_by_human" if approve else "rejected", reply, ticket_id))
        if order_id:
            conn.execute("UPDATE refunds SET status=? WHERE order_id=? AND status='pending_human'",
                         ("approved" if approve else "rejected", order_id))

tab1, tab2, tab3 = st.tabs(["New ticket", "Approval queue", "All tickets"])

with tab1:

    import os

    modes = ["Demo (no API)"] + (["Live (uses Gemini)"] if os.getenv("ENABLE_LIVE") == "1" else []) 
    mode = st.radio("Mode", modes, horizontal=True)
    message = st.text_area("Customer message", "Bro, en order 11 innum varala, refund venum")
    if mode.startswith("Demo"):
        c1, c2, c3, c4 = st.columns(4)
        language = c1.selectbox("Language", ["English", "Tamil", "Tanglish"])
        intent = c2.selectbox("Intent", ["refund", "order_status", "return", "cancel",
                                         "general_query", "complaint"])
        order_id = c3.number_input("Order ID (0 = none)", min_value=0, value=11)
        angry = c4.checkbox("Angry")
    if st.button("Submit ticket"):
        try:
            if mode.startswith("Demo"):
                c = Classification(language=language, intent=intent, urgency="medium",
                                   angry=angry, order_id=order_id or None,
                                   english_query=message)
                r = process(c, message, use_llm=False)
            else:
                r = handle_ticket(message)
            st.success(f"Ticket #{r['ticket_id']} -> {r['status']} ({r['action']})")
            st.info(r["reply"])
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    with get_conn() as conn:
        pending = [dict(r) for r in conn.execute(
            "SELECT * FROM tickets WHERE status='pending_human' ORDER BY id DESC")]
    st.write(f"{len(pending)} ticket(s) waiting for a human")
    for t in pending:
        with st.expander(f"Ticket #{t['id']} | {t['intent']} | order {t['order_id']}"):
            st.write("**Customer:**", t["message"])
            if t["order_id"]:
                with get_conn() as conn:
                    ref = conn.execute(
                        "SELECT amount, status FROM refunds WHERE order_id=? "
                        "ORDER BY id DESC LIMIT 1", (t["order_id"],)).fetchone()
                if ref:
                    st.warning(f"Refund Rs {ref['amount']:.0f} is '{ref['status']}'")
            reply = st.text_area("Reply to customer", t["agent_reply"], key=f"r{t['id']}")
            a, b = st.columns(2)
            if a.button("Approve", key=f"a{t['id']}"):
                resolve(t["id"], t["order_id"], True, reply)
                st.rerun()
            if b.button("Reject", key=f"b{t['id']}"):
                resolve(t["id"], t["order_id"], False, reply)
                st.rerun()

with tab3:
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM tickets ORDER BY id DESC")]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)