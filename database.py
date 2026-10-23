import sqlite3

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    # Foydalanuvchilar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0
        )
    """)
    
    # Buyurtmalar tarixi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game TEXT,
            product TEXT,
            player_id TEXT,
            status TEXT
        )
    """)
    
    # Mahsulotlar va narxlar jadvali (Admin o'zgartirishi uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game TEXT,
            product_name TEXT,
            price INTEGER
        )
    """)
    
    # Agar jadval bo'sh bo'lsa, boshlang'ich mahsulotlarni kiritib qo'yamiz
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        default_products = [
            ("pubg", "60 UC", 10000),
            ("pubg", "325 UC", 50000),
            ("ff", "100 Diamond", 9000),
            ("mlbb", "11 Diamonds", 2000),
            ("standoff", "100 Gold", 12000),
            ("telegram", "50 Stars", 15000),
            ("subscribers", "100 ta Obunachi", 6000)
        ]
        cursor.executemany("INSERT INTO products (game, product_name, price) VALUES (?, ?, ?)", default_products)

    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def update_balance(user_id, amount):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_products(game):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_name, price FROM products WHERE game = ?", (game,))
    res = cursor.fetchall()
    conn.close()
    return res

def add_product(game, name, price):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (game, product_name, price) VALUES (?, ?, ?)", (game, name, price))
    conn.commit()
    conn.close()

def update_product_price(product_id, new_price):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    conn.commit()
    conn.close()

def save_order(user_id, game, product, player_id, status="Success"):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, game, product, player_id, status) VALUES (?, ?, ?, ?, ?)",
                   (user_id, game, product, player_id, status))
    conn.commit()
    conn.close()
