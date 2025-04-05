import sqlite3

DATABASE_NAME = "orders.db"  # Bazaning yagona nomi

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # 'orders' jadvalini yaratish
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            description TEXT,
            language TEXT,
            price INTEGER,
            deadline TEXT,
            status TEXT DEFAULT 'Ochiq' CHECK(status IN ('Ochiq', 'Qabul qilingan')),            user_id INTEGER,
            accepted_by INTEGER DEFAULT NULL
        )
    ''')

    # 'offers' jadvalini yaratish
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            seller_id INTEGER,
            money INTEGER,
            comment TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')

    # Check if money column exists in offers table and add it if it doesn't
    cursor.execute("PRAGMA table_info(offers)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'money' not in columns:
        cursor.execute("ALTER TABLE offers ADD COLUMN money INTEGER")
        print("Added 'money' column to offers table")

    conn.commit()
    conn.close()




# 📌 Yangi buyurtmani qo'shish va ID ni qaytarish
def add_order(order_data, user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (category, description, language, price, deadline, status, user_id)
        VALUES (?, ?, ?, ?, ?, 'Ochiq', ?)
    ''', (
        order_data["category"], order_data["description"], 
        order_data["language"], order_data["price"], 
        order_data["deadline"], user_id
    ))
    conn.commit()
    order_id = cursor.lastrowid  # Yangi qo'shilgan buyurtmaning ID sini olish
    conn.close()
    return order_id






# 📌 Ochiq buyurtmalarni olish
def get_open_orders():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE status = 'Ochiq'")
    orders = cursor.fetchall()
    conn.close()
    return orders

# 📌 Buyurtmani qabul qilish
def accept_order(order_id, user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'Qabul qilingan', accepted_by = ? WHERE id = ?", (user_id, order_id))
    conn.commit()
    conn.close()

# 📌 Buyurtmani ID bo'yicha olish
def get_order_by_id(order_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order


# 📌 Sotuvchining taklifini qo'shish
def add_offer(order_id, seller_id, money, comment):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO offers (order_id, seller_id, money, comment) 
        VALUES (?, ?, ?, ?)
    """, (order_id, seller_id, money, comment))
    conn.commit()
    conn.close()

# 📌 Taklifni qabul qilish
def accept_offer(offer_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Taklifni topish
    cursor.execute("SELECT order_id, seller_id FROM offers WHERE id = ?", (offer_id,))
    offer = cursor.fetchone()

    if offer:
        order_id, seller_id = offer

        # Buyurtma holatini "Qabul qilingan" deb yangilash
        cursor.execute("UPDATE orders SET status = 'Qabul qilingan', accepted_by = ? WHERE id = ?", (seller_id, order_id))

    conn.commit()
    conn.close()


# 📌 Xaridorning barcha buyurtmalarini olish
def get_orders_by_buyer(buyer_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (buyer_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

# 📌 Buyurtmaga berilgan barcha takliflarni olish
def get_offers_by_order(order_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM offers WHERE order_id = ?", (order_id,))
    offers = cursor.fetchall()
    conn.close()
    return offers

# 📌 Muayyan sotuvchining berilgan buyurtmaga bergan taklifini olish
def get_offer_by_seller(order_id, seller_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM offers WHERE order_id = ? AND seller_id = ?", (order_id, seller_id))
    offer = cursor.fetchone()
    conn.close()
    return offer

def accept_offer(order_id, seller_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Buyurtmani qabul qilingan deb yangilash
    cursor.execute("UPDATE orders SET status = 'Qabul qilingan', accepted_by = ? WHERE id = ?", (seller_id, order_id))

    conn.commit()
    conn.close()


import sqlite3

def get_offer_by_order_and_seller(order_id, seller_id):
    # Connect to the database (make sure to replace the path with your actual database path)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Query to get the offer details based on order_id and seller_id
    cursor.execute("""
        SELECT * FROM offers
        WHERE order_id = ? AND seller_id = ?
    """, (order_id, seller_id))

    # Fetch the offer from the database
    offer = cursor.fetchone()

    # Close the connection
    conn.close()

    if offer:
        # You can return the offer as a dictionary or a tuple depending on your needs
        return {
            'price': offer[2],   # Assuming the price is in the 3rd column
            'comment': offer[3],  # Assuming the comment is in the 4th column
            'seller_name': offer[4]  # Assuming the seller's name is in the 5th column
        }
    else:
        return None


import sqlite3

def get_offers_for_order(order_id):
    # SQLite bazasiga ulanish
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Buyurtmaga oid barcha takliflarni olish
    cursor.execute("SELECT seller_id, money, comment FROM offers WHERE order_id = ?", (order_id,))
    offers = cursor.fetchall()

    # Takliflar mavjudligini tekshirish
    if not offers:
        return []

    # Takliflarni ro‘yxatga olish
    result = []
    for offer in offers:
        result.append({
            "seller_id": offer[0],
            "money": offer[1],
            "comment": offer[2],
            # Qo‘shimcha ma'lumotlar, masalan, sotuvchining ismi:
            "seller_name": get_seller_name(offer[0])  # Yangi funksiya qo‘shish
        })

    conn.close()
    return result

def get_seller_name(seller_id):
    # Seller ismini olish
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE user_id = ?", (seller_id,))
    seller = cursor.fetchone()
    conn.close()
    
    return seller[0] if seller else "No Name"








# 📌 Barcha buyurtmalarni olish
def get_orders():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    return orders

# 📌 Foydalanuvchining buyurtmalarini olish
def get_user_orders(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

# 📌 Buyurtmani ID bo‘yicha olish
def get_order_by_id(order_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order



def update_order_status(order_id, status, accepted_by=None):
    """Buyurtma statusini yangilash"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("UPDATE orders SET status = ?, accepted_by = ? WHERE id = ?", (status, accepted_by, order_id))
    conn.commit()
    conn.close()


def get_order_status(order_id):
    """Buyurtmaning statusini olish"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
    order_status = cursor.fetchone()
    conn.close()
    return order_status


def insert_offer(order_id, seller_id, money, comment):
    """Taklifni bazaga qo'shish"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO offers (order_id, seller_id, money, comment) VALUES (?, ?, ?, ?)",
                   (order_id, seller_id, money, comment))
    conn.commit()
    conn.close()


def get_offers(order_id):
    """Buyurtma uchun barcha takliflarni olish"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM offers WHERE order_id = ?", (order_id,))
    offers = cursor.fetchall()
    conn.close()
    return offers