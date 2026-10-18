import io
import random
import contextlib
from app.db import get_conn
from app.agents.classifier import Classification
from app.agents.router import decide
from data.seed_orders import seed

LATE = "julianday(date('now')) - julianday(expected_delivery)"
SINCE = "julianday(date('now')) - julianday(delivered_date)"

SEL = {
    "delayed_small": f"status='delayed' AND amount<=2000 AND {LATE}>5",
    "delayed_big": f"status='delayed' AND amount>2000 AND {LATE}>5",
    "delayed_short": f"status='delayed' AND amount<=2000 AND {LATE}<=5",
    "shipped": "status='shipped'",
    "placed": "status='placed'",
    "delivered": "status='delivered'",
    "delivered_recent": f"status='delivered' AND {SINCE}<=7",
    "delivered_old": f"status='delivered' AND {SINCE}>7",
}

# (name, intent, order selector, angry, query, expected_action, expected_source, repeat)
CASES = [
    ("refund: delayed, small", "refund", "delayed_small", False, "refund please", "refund_approved", None, 1),
    ("refund: delayed, big amount", "refund", "delayed_big", False, "refund please", "escalate", None, 1),
    ("refund: delayed only a few days", "refund", "delayed_short", False, "refund please", "escalate", None, 1),
    ("refund: order already delivered", "refund", "delivered", False, "refund please", "escalate", None, 1),
    ("refund: duplicate request", "refund", "delayed_small", False, "refund please", "refund_exists", None, 2),
    ("refund: angry customer", "refund", "delayed_small", True, "give my money back", "escalate", None, 1),
    ("complaint", "complaint", "shipped", False, "bad service", "escalate", None, 1),
    ("status: shipped", "order_status", "shipped", False, "where is my order", "show_status", None, 1),
    ("status: placed", "order_status", "placed", False, "where is my order", "show_status", None, 1),
    ("cancel: placed", "cancel", "placed", False, "cancel my order", "order_cancelled", None, 1),
    ("cancel: shipped", "cancel", "shipped", False, "cancel my order", "cancel_denied", None, 1),
    ("cancel: delivered", "cancel", "delivered", False, "cancel my order", "cancel_denied", None, 1),
    ("return: recent delivery", "return", "delivered_recent", False, "return this", "return_created", None, 1),
    ("return: old delivery", "return", "delivered_old", False, "return this", "return_denied", None, 1),
    ("return: not delivered", "return", "shipped", False, "return this", "return_denied", None, 1),
    ("missing order id", "refund", "none", False, "refund please", "ask_order_id", None, 1),
    ("unknown order id", "refund", "missing", False, "refund please", "order_not_found", None, 1),
    ("policy: refund timeline", "general_query", "none", False, "How many days does a refund take to reach me?", "answer_from_policy", "refunds.md", 1),
    ("policy: return window", "general_query", "none", False, "What is the return window?", "answer_from_policy", "returns.md", 1),
    ("policy: payment", "general_query", "none", False, "Do you accept UPI?", "answer_from_policy", "faq.md", 1),
    ("policy: cancel after ship", "general_query", "none", False, "Can I cancel after shipping?", "answer_from_policy", "delivery.md", 1),
    ("policy: change address", "general_query", "none", False, "Can I change my delivery address?", "answer_from_policy", "faq.md", 1),
]

def reset():
    random.seed(42)
    with contextlib.redirect_stdout(io.StringIO()):
        seed()

def pick_order(key):
    if key == "none":
        return None
    if key == "missing":
        return 9999
    with get_conn() as conn:
        row = conn.execute(f"SELECT id FROM orders WHERE {SEL[key]} LIMIT 1").fetchone()
    return row["id"] if row else "skip"

def main():
    passed = failed = skipped = 0
    for name, intent, sel, angry, query, expected, src, repeat in CASES:
        reset()
        oid = pick_order(sel)
        if oid == "skip":
            print(f"SKIP  {name} (no matching order in seed data)")
            skipped += 1
            continue
        c = Classification(language="English", intent=intent, urgency="medium",
                           angry=angry, order_id=oid, english_query=query)
        for _ in range(repeat):
            r = decide(c)
        ok = r["action"] == expected
        if ok and src:
            ok = src in [p["source"] for p in r["data"]["policy"]]
        passed += ok
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  -> {r['action']}" + ("" if ok else f"  (expected {expected})"))
    total = passed + failed
    print(f"\n{passed}/{total} passed ({100 * passed / total:.0f}%), {skipped} skipped")

if __name__ == "__main__":
    main()