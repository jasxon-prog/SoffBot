import sqlite3

DATABASE_NAME = "orders.db"

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # 'users' jadvalini yaratish (foydalanuvchilar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT CHECK(role IN ('buyer', 'seller'))  -- seller yoki buyer
        )
    ''')

    # 'orders' jadvalini yaratish (buyurtmalar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            description TEXT,
            language TEXT,
            price INTEGER,
            deadline TEXT,
            status TEXT DEFAULT 'Ochiq' CHECK(status IN ('Ochiq', 'Qabul qilingan')),
            user_id INTEGER,  -- buyurtmachi ID
            accepted_by INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            
        )
    ''')

    # 'offers' jadvalini yaratish (sotuvchilar takliflari)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,  -- buyurtma ID
            seller_id INTEGER,  -- sotuvchi ID
            money INTEGER,
            comment TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (seller_id) REFERENCES users (user_id)
        )
    ''')

    # 'complaints' jadvalini yaratish (shikoyatlar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            complaint_text TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')

    # 'ratings' jadvalini yaratish (baholar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            seller_id INTEGER,
            rating INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (seller_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()




# 📌 Yangi buyurtmani qo'shish va ID ni qaytarish
def add_order(order_data: dict, user_id: int) -> int:
    """
    Yangi buyurtma qo'shadi va uning ID sini qaytaradi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (category, description, language, price, deadline, status, user_id)
        VALUES (?, ?, ?, ?, ?, 'Ochiq', ?)
    ''', (
        order_data["category"],
        order_data["description"],
        order_data["language"],
        order_data["price"],
        order_data["deadline"],
        user_id
    ))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return order_id




def get_orders_by_buyer(user_id: int):
    """
    Xaridorning o'z buyurtmalarini olib keladi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM orders WHERE user_id = ?
    ''', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_orders_by_seller(seller_id: int):
    """
    Sotuvchining qabul qilgan buyurtmalarini olib keladi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM orders WHERE accepted_by = ?
    ''', (seller_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

def get_user_role(user_id: int):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None



# 📌 Buyurtmaga rating qo'shish
def add_rating(order_id, seller_id, rating):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Ratingni ratings jadvaliga qo‘shish
    cursor.execute(
        "INSERT INTO ratings (order_id, seller_id, rating) VALUES (?, ?, ?)",
        (order_id, seller_id, rating)
    )

    conn.commit()
    conn.close()



# 📌 Buyurtmaning bahosini olish
def get_order_rating(order_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT rating FROM orders WHERE id = ?", (order_id,))
    rating = cursor.fetchone()
    
    conn.close()
    
    if rating:
        return rating[0]
    return None



# 📌 Sotuvchining statistikasini olish (shikoyatlarni ham hisoblash)
def get_seller_statistics(seller_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Sotuvchiga tegishli barcha buyurtmalarni olish
    cursor.execute("""
        SELECT o.id, o.status, o.rating, o.complaints
        FROM orders o
        WHERE o.accepted_by = ?
    """, (seller_id,))
    
    orders = cursor.fetchall()

    total_orders = len(orders)
    total_complaints = sum(1 for order in orders if order[3] == 1)  # Shikoyat bor buyurtmalar
    total_rating = sum(order[2] for order in orders if order[2] is not None)  # Rating bo'lgan buyurtmalar

    avg_rating = total_rating / total_orders if total_orders else 0

    conn.close()
    
    return {
        "total_orders": total_orders,
        "total_complaints": total_complaints,
        "avg_rating": avg_rating
    }




def accept_order(order_id: int, user_id: int) -> None:
    """
    Buyurtmani qabul qilish (statusni o'zgartirish va kim qabul qilganini saqlash).
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET status = 'Qabul qilingan', accepted_by = ?
        WHERE id = ?
    ''', (user_id, order_id))
    conn.commit()
    conn.close()


def get_order_by_id(order_id: int):
    """
    Berilgan ID bo'yicha bitta buyurtmani olib keladi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM orders WHERE id = ?
    ''', (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order



def add_offer(order_id: int, seller_id: int, money: int, comment: str) -> None:
    """
    Sotuvchining taklifini qo'shadi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO offers (order_id, seller_id, money, comment)
        VALUES (?, ?, ?, ?)
    ''', (order_id, seller_id, money, comment))
    conn.commit()
    conn.close()




def get_orders_by_buyer(buyer_id: int):
    """
    Xaridorning barcha buyurtmalarini olib keladi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM orders WHERE user_id = ?
    ''', (buyer_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders





def get_user_orders(user_id: int):
    """
    Berilgan foydalanuvchining barcha buyurtmalarini olib keladi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM orders WHERE user_id = ?
    ''', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders




def update_order_status(order_id: int, status: str, accepted_by: int = None) -> None:
    """
    Buyurtma statusini yangilaydi. Agar 'accepted_by' berilgan bo'lsa, 
    buyurtmani kim qabul qilganini ko'rsatadi.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE orders SET status = ?, accepted_by = ? WHERE id = ?
    ''', (status, accepted_by, order_id))
    conn.commit()
    conn.close()





def get_orders_for_page(user_id: int, page: int, items_per_page: int = 10):
    """
    Foydalanuvchining buyurtmalarini sahifalash
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    offset = (page - 1) * items_per_page  # sahifa uchun offset
    cursor.execute('''
        SELECT * FROM orders WHERE user_id = ?
        LIMIT ? OFFSET ?
    ''', (user_id, items_per_page, offset))

    orders = cursor.fetchall()
    conn.close()
    return orders

def get_total_order_count(user_id: int):
    """
    Foydalanuvchining jami buyurtmalari sonini olish
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM orders WHERE user_id = ?
    ''', (user_id,))
    total_orders = cursor.fetchone()[0]
    conn.close()
    return total_orders




def get_seller_id_by_order(order_id):
    """Buyurtma IDsi orqali sotuvchi IDni olish."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT accepted_by FROM orders WHERE id = ?", (order_id,))
    seller_id = cursor.fetchone()

    conn.close()
    if seller_id:
        return seller_id[0]  # Sotuvchi ID
    return None  # Agar sotuvchi topilmasa


# SQLite bazasidan foydalanuvchining rolini olish
def get_user_role(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    role = cursor.fetchone()
    conn.close()
    
    # Agar foydalanuvchi ro'li mavjud bo'lsa, uni qaytaradi
    if role:
        return role[0]
    return None  # Agar fo


def is_order_accepted(order_id: int) -> bool:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None and result[0] == "Qabul qilingan"
