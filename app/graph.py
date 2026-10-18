from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from app.db import get_conn
from app.agents.classifier import classify, Classification
from app.agents.router import decide
from app.agents.writer import write_reply

class TicketState(TypedDict, total=False):
    message: str
    customer_id: Optional[int]
    use_llm: bool
    classification: Classification
    decision: dict
    reply: str
    status: str
    ticket_id: int

def classify_node(state: TicketState):
    if state.get("classification") is not None:   # demo mode: already classified
        return {}
    return {"classification": classify(state["message"])}

def route_node(state: TicketState):
    return {"decision": decide(state["classification"])}

def pick_branch(state: TicketState):
    return "human_review" if state["decision"]["escalate"] else "auto_reply"

def auto_reply_node(state: TicketState):
    reply = write_reply(state["classification"], state["decision"], state.get("use_llm", True))
    return {"reply": reply, "status": "resolved"}

def human_review_node(state: TicketState):
    reply = write_reply(state["classification"], state["decision"], state.get("use_llm", True))
    return {"reply": reply, "status": "pending_human"}

def save_node(state: TicketState):
    c, d = state["classification"], state["decision"]
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tickets (customer_id, order_id, message, language, intent, "
            "status, agent_reply, escalated) VALUES (?,?,?,?,?,?,?,?)",
            (state.get("customer_id"), c.order_id, state["message"], c.language, c.intent,
             state["status"], state["reply"], int(d["escalate"])))
    return {"ticket_id": cur.lastrowid}

builder = StateGraph(TicketState)
builder.add_node("classify", classify_node)
builder.add_node("route", route_node)
builder.add_node("auto_reply", auto_reply_node)
builder.add_node("human_review", human_review_node)
builder.add_node("save", save_node)

builder.add_edge(START, "classify")
builder.add_edge("classify", "route")
builder.add_conditional_edges("route", pick_branch,
                              {"auto_reply": "auto_reply", "human_review": "human_review"})
builder.add_edge("auto_reply", "save")
builder.add_edge("human_review", "save")
builder.add_edge("save", END)

graph = builder.compile()

def run_ticket(message, classification=None, customer_id=None, use_llm=True) -> dict:
    out = graph.invoke({"message": message, "customer_id": customer_id,
                        "use_llm": use_llm, "classification": classification})
    return {"ticket_id": out["ticket_id"], "status": out["status"],
            "action": out["decision"]["action"], "reason": out["decision"]["reason"],
            "reply": out["reply"]}