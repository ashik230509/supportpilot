from app.db import get_conn
from app.tools.orders import get_order_status, create_return
from app.tools.refunds import issue_refund

def first_order(where):
    with get_conn() as conn:
        row = conn.execute(f"SELECT id FROM orders WHERE {where} LIMIT 1").fetchone()
    return row["id"] if row else None

delayed = first_order("status='delayed' AND amount <= 2000")
expensive = first_order("status='delayed' AND amount > 2000")
delivered = first_order("status='delivered'")

print("1. Order status:", get_order_status(delayed))
print("2. Auto refund (should be auto_approved):", issue_refund(delayed, "late delivery"))
print("3. Big refund (should be pending_human):", issue_refund(expensive, "late delivery"))
print("4. Return:", create_return(delivered, "wrong size"))
print("5. Missing order:", get_order_status(9999))