import time
from typing import Literal, Optional
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GOOGLE_API_KEY, MODEL_NAME

class Classification(BaseModel):
    language: Literal["English", "Tamil", "Tanglish"]
    intent: Literal["order_status", "refund", "return", "cancel", "general_query", "complaint"]
    urgency: Literal["low", "medium", "high"]
    angry: bool
    order_id: Optional[int]
    english_query: str

PROMPT = """You are the ticket classifier for an e-commerce support system.
Read the customer message (English, Tamil, or Tanglish = Tamil written in English letters) and fill the fields:
- language: the language the customer wrote in
- intent: the main thing they want (see rules below)
- urgency: high if angry, repeated, or urgent; low for simple questions
- angry: true only if the tone is clearly angry or abusive
- order_id: the order number if mentioned, else null
- english_query: the message rewritten as a clear English sentence

Intent rules:
- refund, return, cancel, order_status: ONLY when the customer wants something done for THEIR OWN order ("I want a refund", "cancel my order", "where is my order").
- general_query: when the customer asks HOW something works, how long it takes, or what the rules are (refund timeline, return window, payment methods, address change), even if the words "refund" or "return" appear. Usually there is no order number.
- complaint: when the main point is dissatisfaction with the service and not a specific request.

Customer message:
"""

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, google_api_key=GOOGLE_API_KEY,
                             temperature=0, max_retries=0)
structured_llm = llm.with_structured_output(Classification)

def classify(message: str, retries: int = 4) -> Classification:
    for attempt in range(retries):
        try:
            return structured_llm.invoke(PROMPT + message)
        except Exception as e:
            msg = str(e)
            if "PerDay" in msg:
                print("DAILY quota finished. Try tomorrow or switch model.")
                raise
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "503" in msg or "UNAVAILABLE" in msg:
                print(f"[temporary limit or server busy, waiting 30s, attempt {attempt+1}]")
                time.sleep(30)
            else:
                raise
    raise RuntimeError("Still blocked after retries")