from app.db import get_conn

ALLOWED = {"intent", "status", "agent_reply", "escalated", "language"}

def update_ticket(ticket_id: int, **fields) -> dict:
    fields = {k: v for k, v in fields.items() if k in ALLOWED}
    if not fields:
        return {"success": False, "error": "No valid fields"}
    sets = ", ".join(f"{k} = ?" for k in fields)
    with get_conn() as conn:
        conn.execute(f"UPDATE tickets SET {sets} WHERE id = ?", (*fields.values(), ticket_id))
    return {"success": True, "ticket_id": ticket_id, **fields}