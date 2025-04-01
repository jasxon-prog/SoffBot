import sqlite3

# 📌 Ma'lumotlar bazasida jadval yaratish
def create_tables():
    conn = sqlite3.connect("orders.db")  # Bazaga ulanish
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            academic_work TEXT,
            work_type TEXT,
            work_size TEXT,
            language TEXT,
            requirements TEXT,
            duration TEXT,
            price TEXT,
            comment TEXT,
            user_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()





def get_user_orders(user_id):
    # Ma'lumotlar bazasiga ulanish
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    # Foydalanuvchi buyurtmalarini olish
    cursor.execute("SELECT * FROM orders WHERE user_id=?", (user_id,))
    orders = cursor.fetchall()

    conn.close()

    return orders




# 📌 Yangi buyurtmani qo‘shish
def add_order(order_data, user_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO orders (academic_work, work_type, work_size, language, 
                        requirements, duration, price, comment, user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    order_data["academic_work"], order_data["work_type"], order_data["work_size"],
    order_data["language"], order_data["requirements"], order_data["duration"],
    order_data["price"], order_data["comment"], user_id  # Endi to‘g‘ri ishlaydi!
))
    conn.commit()
    conn.close()

# 📌 Barcha buyurtmalarni olish
def get_orders():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    return orders

# 📌 Foydalanuvchining buyurtmalarini olish
def get_user_orders(user_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders

# 📌 Buyurtmani ID bo‘yicha olish
def get_order_by_id(order_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order

# 📌 Buyurtmani ID bo‘yicha o‘chirish
def delete_order(order_id):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

# 📌 Buyurtmani yangilash
def update_order(order_id, updated_data):
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET academic_work = ?, work_type = ?, work_size = ?, language = ?, 
            requirements = ?, duration = ?, price = ?, comment = ?
        WHERE id = ?
    ''', (
        updated_data["academic_work"], updated_data["work_type"], updated_data["work_size"],
        updated_data["language"], updated_data["requirements"], updated_data["duration"],
        updated_data["price"], updated_data["comment"], order_id
    ))
    conn.commit()
    conn.close()


