from app.agents.classifier import llm

def template_reply(c, d) -> str:
    a, data = d["action"], d["data"]
    if a == "refund_approved":
        return (f"Sorry for the delay. Your refund of Rs {data['refund']['amount']:.0f} "
                f"for order {c.order_id} is approved and will reach you in 5 to 7 working days.")
    if a == "refund_exists":
        r = data["refund"]
        if r["previous_status"] == "pending_human":
            return (f"Your refund request of Rs {r['amount']:.0f} for order {c.order_id} "
                    f"is already with a human agent for review. You will hear back within 24 hours.")
        return (f"A refund of Rs {r['amount']:.0f} for order {c.order_id} was already "
                f"requested (status: {r['previous_status']}). No need to request again.")
    if a == "escalate":
        return ("Thanks for reaching out. We have passed your request to a human agent "
                "who will reply within 24 hours.")
    if a == "show_status":
        o = data["order"]
        return (f"Order {o['id']} ({o['product_name']}) is '{o['status']}'. "
                f"Expected delivery: {o['expected_delivery']}.")
    if a == "ask_order_id":
        return "Please share your order ID so I can help you."
    if a == "order_not_found":
        return f"I could not find order {data['order_id']}. Please check the order ID."
    if a == "return_created":
        return f"Your return for order {c.order_id} is created. Pickup will be scheduled within 2 days."
    if a == "return_denied":
        return f"Sorry, this return cannot be created: {data['return']['error']}."
    if a == "order_cancelled":
        return f"Your order {c.order_id} has been cancelled."
    if a == "cancel_denied":
        return f"Sorry, this order cannot be cancelled: {data['cancel']['error']}."
    if a == "answer_from_policy":
        chunks = [p["text"].split("\n", 1)[-1].strip() for p in data["policy"][:2]]
        return " ".join(chunks)
    return "A human agent will contact you soon."

def write_reply(c, d, use_llm: bool = True) -> str:
    base = template_reply(c, d)
    if not use_llm or c.language == "English":
        return base
    prompt = (f"Rewrite this customer support reply in {c.language} "
              f"({'Tamil script' if c.language == 'Tamil' else 'Tamil written in English letters, casual'}). "
              "Keep it short and polite. Do NOT add, remove or change any facts, numbers, "
              "amounts or order IDs. Output only the reply.\n\nReply:\n" + base)
    try:
        resp = llm.invoke(prompt).content
        text = resp if isinstance(resp, str) else "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in resp)
        return text.strip() or base
    except Exception:
        return base