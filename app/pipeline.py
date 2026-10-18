from app.db import get_conn
from app.graph import run_ticket


def process(c, message: str, customer_id=None, use_llm=True) -> dict:
    """Run a ticket through the LangGraph workflow with a ready classification (demo mode)."""
    return run_ticket(message, classification=c, customer_id=customer_id, use_llm=use_llm)


def handle_ticket(message: str, customer_id=None) -> dict:
    """Run a ticket through the LangGraph workflow, classifying with Gemini (live mode)."""
    return run_ticket(message, customer_id=customer_id)


def resolve_ticket(ticket_id: int, approve: bool, reply=None):
    """Human approves or rejects a ticket waiting in the approval queue."""
    with get_conn() as conn:
        t = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if t is None:
            return None
        if t["status"] != "pending_human":
            return {"error": f"Ticket is '{t['status']}', not pending_human"}
        new_status = "resolved_by_human" if approve else "rejected"
        final_reply = reply or t["agent_reply"]
        conn.execute("UPDATE tickets SET status=?, agent_reply=? WHERE id=?",
                     (new_status, final_reply, ticket_id))
        if t["order_id"]:
            conn.execute(
                "UPDATE refunds SET status=? WHERE order_id=? AND status='pending_human'",
                ("approved" if approve else "rejected", t["order_id"]))
    return {"ticket_id": ticket_id, "status": new_status, "reply": final_reply}