from app.agents.classifier import Classification
from app.pipeline import process
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

cases = [
    make("refund", small),
    make("refund", big),
    make("refund", small, angry=True),
    make("order_status", shipped),
    make("refund", None),
    make("general_query", None, query="How long do I have to return an item?"),
]

for c in cases:
    r = process(c, f"test: {c.intent}", use_llm=False)
    print(f"\n[{r['status']}] {r['action']}\n  -> {r['reply']}")