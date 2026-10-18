from app.rag.retriever import retrieve

questions = [
    "My order is late, can I get a refund?",
    "How long do I have to return an item?",
    "Can I cancel after shipping?",
    "What payment options do you have?",
    "Refund above 2000 rupees who approves?",
]


for q in questions:
    print(f"\nQ: {q}")
    for r in retrieve(q, k=2):
        print(f"  [{r['source']} | {r['distance']}] {r['text'][:90]!r}")