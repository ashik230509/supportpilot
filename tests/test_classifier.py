import time
from app.agents.classifier import classify

tickets = [
    "Bro, en order 11 innum varala, refund venum",
    "Where is my order 25? It was supposed to come last week.",
    "என் ஆர்டர் 8 ரத்து செய்ய வேண்டும்",
    "This is the WORST service!! I want my money back for order 3 NOW",
    "What payment methods do you accept?",
]

for t in tickets:
    print(f"\n{t}")
    print(classify(t))
    time.sleep(14)