import random
from datetime import date, timedelta
from app.db import get_conn, init_db

random.seed(42)

NAMES = ["Arun", "Divya", "Karthik", "Priya", "Suresh", "Meena", "Vignesh",
         "Lakshmi", "Ravi", "Anitha", "Mohan", "Kavya", "Sathish", "Nithya",
         "Harish", "Deepa", "Gokul", "Swetha", "Bala", "Janani"]
LANGS = ["Tamil", "English", "Tanglish"]
PRODUCTS = [("Wireless Earbuds", 1499), ("Running Shoes", 2499),
            ("Cotton Kurta", 799), ("Phone Case", 299),
            ("Smart Watch", 4999), ("Backpack", 1199),
            ("Mixer Grinder", 3299), ("Water Bottle", 399)]

def seed():
    init_db()
    today = date.today()
    with get_conn() as conn:
        for t in ("refunds", "tickets", "orders", "customers"):
            conn.execute(f"DELETE FROM {t}")

        for i, name in enumerate(NAMES, start=1):
            conn.execute(
                "INSERT INTO customers VALUES (?,?,?,?,?)",
                (i, name, f"{name.lower()}@example.com",
                 f"98{random.randint(10000000, 99999999)}", random.choice(LANGS)))

        for oid in range(1, 51):
            product, amount = random.choice(PRODUCTS)
            status = random.choice(
                ["delivered", "shipped", "delayed", "delayed", "cancelled", "placed"])
            order_date = today - timedelta(days=random.randint(3, 20))
            expected = order_date + timedelta(days=5)
            delivered = None
            if status == "delivered":
                delivered = expected - timedelta(days=random.randint(0, 2))
            elif status == "delayed":
                expected = today - timedelta(days=random.randint(3, 10))
            conn.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)",
                (oid, random.randint(1, len(NAMES)), product, amount, status,
                 order_date.isoformat(), expected.isoformat(),
                 delivered.isoformat() if delivered else None))
    print("Seeded 20 customers and 50 orders")

if __name__ == "__main__":
    seed()