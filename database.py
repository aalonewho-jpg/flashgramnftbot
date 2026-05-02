import sqlite3
from datetime import datetime, timedelta

DB_PATH = "flashgram.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        flashgram_username TEXT,
        flashgram_phone TEXT,
        ref_by INTEGER DEFAULT 0,
        stars_balance INTEGER DEFAULT 0,
        last_free_case TIMESTAMP,
        reg_date TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_name TEXT,
        obtained_date TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        date TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_name TEXT,
        status TEXT DEFAULT 'pending',
        request_date TIMESTAMP,
        thread_id INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS promocodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        reward_type TEXT,
        reward_value TEXT,
        uses_left INTEGER,
        created_by INTEGER,
        created_date TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS shop_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        nft_name TEXT,
        color TEXT,
        status TEXT DEFAULT 'pending',
        price INTEGER DEFAULT 0,
        link TEXT DEFAULT '',
        thread_id INTEGER DEFAULT 0,
        created_date TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, ref_by=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO users (user_id, username, ref_by, last_free_case, reg_date)
                 VALUES (?, ?, ?, ?, ?)''',
              (user_id, username, ref_by or 0, datetime.now() - timedelta(days=1), datetime.now()))
    conn.commit()
    conn.close()

def update_flashgram_data(user_id, flashgram_username, flashgram_phone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET flashgram_username = ?, flashgram_phone = ? WHERE user_id = ?",
              (flashgram_username, flashgram_phone, user_id))
    conn.commit()
    conn.close()

def remove_one_case(user_id, case_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM inventory WHERE user_id = ? AND item_name = ? LIMIT 1", (user_id, case_name))
    row = c.fetchone()
    if row:
        c.execute("DELETE FROM inventory WHERE id = ?", (row[0],))
    conn.commit()
    conn.close()

def add_stars(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def remove_stars(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET stars_balance = stars_balance - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_stars(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT stars_balance FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def add_to_inventory(user_id, item_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO inventory (user_id, item_name, obtained_date) VALUES (?, ?, ?)",
              (user_id, item_name, datetime.now()))
    conn.commit()
    conn.close()

def remove_from_inventory(user_id, item_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM inventory WHERE user_id = ? AND item_name = ? LIMIT 1", (user_id, item_name))
    row = c.fetchone()
    if row:
        c.execute("DELETE FROM inventory WHERE id = ?", (row[0],))
    conn.commit()
    conn.close()

def get_inventory(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT item_name FROM inventory WHERE user_id = ?", (user_id,))
    items = [row[0] for row in c.fetchall()]
    conn.close()
    return items

def get_referral_count(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def add_referral(referrer_id, referred_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)",
              (referrer_id, referred_id, datetime.now()))
    conn.commit()
    conn.close()

def get_top_refs(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT users.username, COUNT(referrals.id) as ref_count 
                 FROM users 
                 LEFT JOIN referrals ON users.user_id = referrals.referrer_id 
                 GROUP BY users.user_id 
                 ORDER BY ref_count DESC 
                 LIMIT ?''', (limit,))
    top = c.fetchall()
    conn.close()
    return top

def update_last_free_case(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET last_free_case = ? WHERE user_id = ?", (datetime.now(), user_id))
    conn.commit()
    conn.close()

def get_last_free_case(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT last_free_case FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return datetime.fromisoformat(result[0]) if result and result[0] else None

def add_withdrawal(user_id, item_name, thread_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO withdrawals (user_id, item_name, request_date, thread_id) VALUES (?, ?, ?, ?)",
              (user_id, item_name, datetime.now(), thread_id))
    conn.commit()
    conn.close()

# Функции для промокодов
def add_promocode(code, reward_type, reward_value, uses_left, created_by):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO promocodes (code, reward_type, reward_value, uses_left, created_by, created_date) VALUES (?, ?, ?, ?, ?, ?)",
              (code, reward_type, reward_value, uses_left, created_by, datetime.now()))
    conn.commit()
    conn.close()

def get_promocode(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM promocodes WHERE code = ?", (code,))
    promo = c.fetchone()
    conn.close()
    return promo

def use_promocode(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()

def delete_promocode(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM promocodes WHERE code = ?", (code,))
    conn.commit()
    conn.close()

# Функции для магазина
def add_shop_order(user_id, nft_name, color, thread_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO shop_orders (user_id, nft_name, color, thread_id, created_date) VALUES (?, ?, ?, ?, ?)",
              (user_id, nft_name, color, thread_id, datetime.now()))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_shop_order(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM shop_orders WHERE id = ?", (order_id,))
    order = c.fetchone()
    conn.close()
    return order

def update_shop_order_price(order_id, price):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE shop_orders SET price = ? WHERE id = ?", (price, order_id))
    conn.commit()
    conn.close()

def update_shop_order_link(order_id, link):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE shop_orders SET link = ? WHERE id = ?", (link, order_id))
    conn.commit()
    conn.close()

def update_shop_order_status(order_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE shop_orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

def delete_inventory_item_by_id(item_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
