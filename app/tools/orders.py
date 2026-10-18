from datetime import date
from app.db import get_conn

def get_order_status(order_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return {"found": False, "error": f"Order {order_id} not found"}

    order = dict(row)
    order["found"] = True
    order["days_late"] = 0
    if order["status"] in ("delayed", "shipped", "placed"):
        late = (date.today() - date.fromisoformat(order["expected_delivery"])).days
        order["days_late"] = max(late, 0)
    return order

def create_return(order_id: int, reason: str) -> dict:
    order = get_order_status(order_id)
    if not order["found"]:
        return order
    if order["status"] != "delivered":
        return {"success": False, "error": "Only delivered orders can be returned"}
    days_since = (date.today() - date.fromisoformat(order["delivered_date"])).days
    if days_since > 7:
        return {"success": False, "error": "Return window (7 days) is over"}
    return {"success": True, "message": f"Return created for order {order_id}", "reason": reason}
def cancel_order(order_id: int) -> dict:
    order = get_order_status(order_id)
    if not order["found"]:
        return order
    if order["status"] != "placed":
        return {"success": False,
                "error": f"Order is '{order['status']}'. Only orders not yet shipped can be cancelled"}
    with get_conn() as conn:
        conn.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
    return {"success": True, "message": f"Order {order_id} cancelled"}