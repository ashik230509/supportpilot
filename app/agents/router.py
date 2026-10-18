from app.agents.classifier import Classification
from app.tools.orders import get_order_status, create_return, cancel_order
from app.tools.refunds import issue_refund
from app.rag.retriever import retrieve

def result(action, escalate=False, reason="", data=None):
    return {"action": action, "escalate": escalate, "reason": reason, "data": data or {}}

def decide(c: Classification) -> dict:
    # 1. Risky cases go straight to a human
    if c.angry or c.intent == "complaint":
        return result("escalate", True, "angry customer or complaint")

    # 2. Policy questions use RAG (searched in English)
    if c.intent == "general_query":
        return result("answer_from_policy", data={"policy": retrieve(c.english_query, k=3)})

    # 3. Everything else needs an order id
    if c.order_id is None:
        return result("ask_order_id", reason="order id missing")

    order = get_order_status(c.order_id)
    if not order["found"]:
        return result("order_not_found", data={"order_id": c.order_id})

    if c.intent == "order_status":
        return result("show_status", data={"order": order})

    if c.intent == "refund":
        refund = issue_refund(c.order_id, c.english_query)
        if refund["status"] == "already_requested":
            return result("refund_exists", data={"refund": refund, "order": order})
        if refund["status"] == "auto_approved":
            return result("refund_approved", data={"refund": refund, "order": order})
        return result("escalate", True, "refund needs human approval",
                      {"refund": refund, "order": order})

    if c.intent == "return":
        ret = create_return(c.order_id, c.english_query)
        return result("return_created" if ret["success"] else "return_denied",
                      data={"return": ret, "order": order})

    if c.intent == "cancel":
        res = cancel_order(c.order_id)
        return result("order_cancelled" if res["success"] else "cancel_denied",
                      data={"cancel": res, "order": order})

    return result("escalate", True, "unknown case")