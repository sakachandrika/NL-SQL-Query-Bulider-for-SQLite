"""
create_db.py — builds sales.db with realistic sample data
Tables: customers, products, orders, order_items
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "sales.db"

FIRST_NAMES = ["Alice","Bob","Carol","David","Emma","Frank","Grace","Henry","Iris","Jack",
               "Karen","Liam","Mia","Noah","Olivia","Paul","Quinn","Rachel","Sam","Tina",
               "Uma","Victor","Wendy","Xavier","Yara","Zane","Amber","Blake","Chloe","Dylan",
               "Eva","Finn","Gina","Hugo","Isla","Jake","Kira","Leo","Maya","Nate",
               "Opal","Pete","Rosa","Seth","Tara","Uri","Vera","Will","Xena","Yuna"]

LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Moore",
              "Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Lee","Walker",
              "Hall","Allen","Young","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
              "Green","Adams","Nelson","Baker","Carter","Mitchell","Perez","Roberts","Turner","Phillips",
              "Campbell","Parker","Evans","Edwards","Collins","Stewart","Sanchez","Morris","Rogers","Reed"]

CITIES = [("New York","NY"),("Los Angeles","CA"),("Chicago","IL"),("Houston","TX"),("Phoenix","AZ"),
          ("Philadelphia","PA"),("San Antonio","TX"),("San Diego","CA"),("Dallas","TX"),("San Jose","CA"),
          ("Austin","TX"),("Jacksonville","FL"),("Fort Worth","TX"),("Columbus","OH"),("Charlotte","NC"),
          ("Indianapolis","IN"),("San Francisco","CA"),("Seattle","WA"),("Denver","CO"),("Nashville","TN")]

PRODUCTS = [
    ("Laptop Pro 15","Electronics",1299.99,"High-performance laptop"),
    ("Wireless Mouse","Electronics",29.99,"Ergonomic wireless mouse"),
    ("USB-C Hub","Electronics",49.99,"7-in-1 USB-C hub"),
    ("Mechanical Keyboard","Electronics",119.99,"Clicky mechanical keyboard"),
    ("4K Monitor","Electronics",399.99,"27-inch 4K display"),
    ("Webcam HD","Electronics",79.99,"1080p webcam"),
    ("Noise Cancelling Headphones","Electronics",249.99,"Over-ear ANC headphones"),
    ("Standing Desk","Furniture",549.99,"Electric height-adjustable desk"),
    ("Office Chair","Furniture",329.99,"Ergonomic mesh chair"),
    ("Desk Lamp","Furniture",39.99,"LED adjustable lamp"),
    ("Bookshelf","Furniture",149.99,"5-shelf wooden bookshelf"),
    ("File Cabinet","Furniture",199.99,"3-drawer metal cabinet"),
    ("Notebook A5","Stationery",8.99,"200-page lined notebook"),
    ("Ballpoint Pens 12pk","Stationery",5.99,"Smooth writing pens"),
    ("Sticky Notes 10pk","Stationery",4.49,"Assorted color sticky notes"),
    ("Whiteboard 36x24","Stationery",34.99,"Dry-erase whiteboard"),
    ("Stapler","Stationery",12.99,"Heavy-duty stapler"),
    ("Paper Shredder","Electronics",89.99,"Cross-cut paper shredder"),
    ("Label Maker","Electronics",44.99,"Handheld label maker"),
    ("Calculator","Stationery",14.99,"Scientific calculator"),
    ("Coffee Maker","Kitchen",79.99,"12-cup drip coffee maker"),
    ("Electric Kettle","Kitchen",34.99,"1.7L fast-boil kettle"),
    ("Mini Fridge","Kitchen",149.99,"2.5 cu ft compact fridge"),
    ("Microwave","Kitchen",89.99,"700W countertop microwave"),
    ("Water Filter Pitcher","Kitchen",24.99,"10-cup Brita-style pitcher"),
    ("Backpack","Accessories",59.99,"17-inch laptop backpack"),
    ("Tote Bag","Accessories",19.99,"Canvas tote bag"),
    ("Phone Stand","Accessories",9.99,"Adjustable phone/tablet stand"),
    ("Cable Management Kit","Accessories",15.99,"Velcro straps and clips"),
    ("Screen Cleaner Kit","Accessories",7.99,"Spray + microfiber cloth"),
    ("External SSD 1TB","Electronics",99.99,"USB-C portable SSD"),
    ("Smart Speaker","Electronics",59.99,"Voice-controlled smart speaker"),
    ("Tablet 10in","Electronics",329.99,"Android 10-inch tablet"),
    ("Smartphone Stand Wireless","Electronics",39.99,"Qi wireless charging stand"),
    ("Laser Pointer","Stationery",12.99,"Presentation laser pointer"),
    ("Monitor Arm","Furniture",69.99,"Single monitor arm"),
    ("Footrest","Furniture",44.99,"Adjustable ergonomic footrest"),
    ("Desk Mat","Accessories",24.99,"Large leather desk mat"),
    ("Drawer Organizer","Accessories",17.99,"6-compartment drawer tray"),
    ("Surge Protector 8-outlet","Electronics",29.99,"8-outlet surge protector"),
    ("HDMI Cable 6ft","Electronics",9.99,"4K HDMI 2.0 cable"),
    ("Extension Cord 10ft","Electronics",14.99,"3-outlet extension cord"),
    ("AA Batteries 24pk","Accessories",11.99,"Alkaline AA batteries"),
    ("AAA Batteries 20pk","Accessories",9.99,"Alkaline AAA batteries"),
    ("Printer Ink Black","Stationery",16.99,"Compatible black ink cartridge"),
    ("Printer Ink Color","Stationery",18.99,"Compatible color ink cartridge"),
    ("Copy Paper 500 sheets","Stationery",6.99,"Letter-size copy paper ream"),
    ("Envelopes 100pk","Stationery",7.99,"#10 business envelopes"),
    ("Index Cards 200pk","Stationery",3.99,"3x5 ruled index cards"),
    ("Tape Dispenser","Stationery",6.49,"Desktop tape dispenser"),
]


def create_database():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── Schema ──────────────────────────────────────────────────────────────
    cur.executescript("""
    CREATE TABLE customers (
        customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name    TEXT NOT NULL,
        last_name     TEXT NOT NULL,
        email         TEXT UNIQUE NOT NULL,
        city          TEXT,
        state         TEXT,
        signup_date   DATE NOT NULL,
        is_premium    INTEGER DEFAULT 0   -- 0=regular, 1=premium
    );

    CREATE TABLE products (
        product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name  TEXT NOT NULL,
        category      TEXT NOT NULL,
        unit_price    REAL NOT NULL,
        description   TEXT,
        stock_qty     INTEGER DEFAULT 100
    );

    CREATE TABLE orders (
        order_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
        order_date    DATE NOT NULL,
        status        TEXT NOT NULL DEFAULT 'completed',
        shipping_city TEXT,
        shipping_state TEXT,
        total_amount  REAL
    );

    CREATE TABLE order_items (
        item_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id      INTEGER NOT NULL REFERENCES orders(order_id),
        product_id    INTEGER NOT NULL REFERENCES products(product_id),
        quantity      INTEGER NOT NULL DEFAULT 1,
        unit_price    REAL NOT NULL,
        subtotal      REAL GENERATED ALWAYS AS (quantity * unit_price) STORED
    );

    CREATE INDEX idx_orders_date      ON orders(order_date);
    CREATE INDEX idx_orders_customer  ON orders(customer_id);
    CREATE INDEX idx_items_order      ON order_items(order_id);
    CREATE INDEX idx_items_product    ON order_items(product_id);
    """)

    # ── Customers (100) ─────────────────────────────────────────────────────
    customers = []
    used_emails = set()
    for i in range(100):
        fn = FIRST_NAMES[i % len(FIRST_NAMES)]
        ln = LAST_NAMES[i % len(LAST_NAMES)]
        base = f"{fn.lower()}.{ln.lower()}"
        email = f"{base}@example.com"
        n = 1
        while email in used_emails:
            email = f"{base}{n}@example.com"
            n += 1
        used_emails.add(email)
        city, state = random.choice(CITIES)
        days_ago = random.randint(30, 730)
        signup = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        is_premium = 1 if random.random() < 0.2 else 0
        customers.append((fn, ln, email, city, state, signup, is_premium))

    cur.executemany(
        "INSERT INTO customers(first_name,last_name,email,city,state,signup_date,is_premium) VALUES(?,?,?,?,?,?,?)",
        customers
    )

    # ── Products (50) ────────────────────────────────────────────────────────
    cur.executemany(
        "INSERT INTO products(product_name,category,unit_price,description) VALUES(?,?,?,?)",
        PRODUCTS
    )

    # ── Orders + order_items (500 orders) ───────────────────────────────────
    statuses = ["completed", "completed", "completed", "shipped", "pending", "refunded"]
    order_rows = []
    item_rows  = []
    order_id   = 1

    for _ in range(500):
        cust_id    = random.randint(1, 100)
        days_ago   = random.randint(0, 365)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        status     = random.choice(statuses)
        city, state = random.choice(CITIES)

        num_items  = random.randint(1, 5)
        prod_ids   = random.sample(range(1, 51), min(num_items, 50))
        total      = 0.0
        items_for_order = []
        for pid in prod_ids:
            price = PRODUCTS[pid - 1][2]
            qty   = random.randint(1, 4)
            total += price * qty
            items_for_order.append((order_id, pid, qty, price))

        order_rows.append((cust_id, order_date, status, city, state, round(total, 2)))
        item_rows.extend(items_for_order)
        order_id += 1

    cur.executemany(
        "INSERT INTO orders(customer_id,order_date,status,shipping_city,shipping_state,total_amount) VALUES(?,?,?,?,?,?)",
        order_rows
    )
    cur.executemany(
        "INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES(?,?,?,?)",
        item_rows
    )

    conn.commit()
    conn.close()
    print(f"✅  sales.db created at {DB_PATH}")
    print(f"    customers : 100")
    print(f"    products  : 50")
    print(f"    orders    : 500")
    print(f"    items     : {len(item_rows)}")


if __name__ == "__main__":
    create_database()
