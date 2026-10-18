from app.db import get_conn
from app.tools.orders import get_order_status

AUTO_REFUND_LIMIT = 2000   # rupees
MIN_DELAY_DAYS = 5

def issue_refund(order_id: int, reason: str) -> dict:
    order = get_order_status(order_id)
    if not order["found"]:
        return order
    
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT status, amount FROM refunds WHERE order_id = ? AND status != 'rejected'",
            (order_id,)).fetchone()
    if existing:
        return {"order_id": order_id, "amount": existing["amount"],
                "status": "already_requested", "previous_status": existing["status"]}

    eligible = order["status"] == "delayed" and order["days_late"] > MIN_DELAY_DAYS
    amount = order["amount"]

    if eligible and amount <= AUTO_REFUND_LIMIT:
        status = "auto_approved"
    else:
        status = "pending_human"

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO refunds (order_id, amount, reason, status) VALUES (?,?,?,?)",
            (order_id, amount, reason, status))
    return {"order_id": order_id, "amount": amount, "status": status}