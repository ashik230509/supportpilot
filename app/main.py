from typing import Optional, Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.db import get_conn, init_db
from app.agents.classifier import Classification
from app.pipeline import process, handle_ticket, resolve_ticket

init_db()
app = FastAPI(title="SupportPilot API", version="1.0")

class TicketIn(BaseModel):
    message: str
    customer_id: Optional[int] = None

class DemoTicketIn(BaseModel):
    message: str
    language: Literal["English", "Tamil", "Tanglish"] = "English"
    intent: Literal["order_status", "refund", "return", "cancel",
                    "general_query", "complaint"] = "refund"
    order_id: Optional[int] = None
    angry: bool = False

class ResolveIn(BaseModel):
    reply: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tickets")
def create_ticket(body: TicketIn):
    """Live mode: the classifier calls Gemini."""
    try:
        return handle_ticket(body.message, body.customer_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM unavailable: {str(e)[:200]}")

@app.post("/tickets/demo")
def create_demo_ticket(body: DemoTicketIn):
    """Demo mode: you provide the classification, so no LLM call is used."""
    c = Classification(language=body.language, intent=body.intent, urgency="medium",
                       angry=body.angry, order_id=body.order_id,
                       english_query=body.message)
    return process(c, body.message, use_llm=False)

@app.get("/tickets")
def list_tickets(status: Optional[str] = None):
    query, args = "SELECT * FROM tickets", ()
    if status:
        query, args = query + " WHERE status=?", (status,)
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query + " ORDER BY id DESC", args)]

@app.get("/tickets/pending")
def pending_tickets():
    return list_tickets(status="pending_human")

@app.post("/tickets/{ticket_id}/approve")
def approve(ticket_id: int, body: ResolveIn = ResolveIn()):
    res = resolve_ticket(ticket_id, True, body.reply)
    if res is None:
        raise HTTPException(404, "Ticket not found")
    if "error" in res:
        raise HTTPException(409, res["error"])
    return res

@app.post("/tickets/{ticket_id}/reject")
def reject(ticket_id: int, body: ResolveIn = ResolveIn()):
    res = resolve_ticket(ticket_id, False, body.reply)
    if res is None:
        raise HTTPException(404, "Ticket not found")
    if "error" in res:
        raise HTTPException(409, res["error"])
    return res