from app.agents.classifier import Classification
from app.agents.router import decide
from app.db import get_conn

def first_order(where):
    with get_conn() as conn:
        row = conn.execute(f"SELECT id FROM orders WHERE {where} LIMIT 1").fetchone()
    return row["id"] if row else None

def make(intent, order_id=None, angry=False, query="test"):
    return Classification(language="English", intent=intent, urgency="medium",
                          angry=angry, order_id=order_id, english_query=query)

small = first_order("status='delayed' AND amount <= 2000")
big = first_order("status='delayed' AND amount > 2000")
shipped = first_order("status='shipped'")
placed = first_order("status='placed'")

cases = [
    ("1 small delayed refund -> refund_approved", make("refund", small)),
    ("2 big refund -> escalate", make("refund", big)),
    ("3 angry customer -> escalate", make("refund", small, angry=True)),
    ("4 order status -> show_status", make("order_status", shipped)),
    ("5 no order id -> ask_order_id", make("refund", None)),
    ("6 order 9999 -> order_not_found", make("refund", 9999)),
    ("7 cancel shipped -> cancel_denied", make("cancel", shipped)),
    ("8 cancel placed -> order_cancelled", make("cancel", placed)),
    ("9 policy question -> answer_from_policy",
     make("general_query", None, query="What payment methods do you accept?")),
]

for name, c in cases:
    r = decide(c)
    print(f"{name}\n   action={r['action']}  escalate={r['escalate']}  reason={r['reason']!r}")