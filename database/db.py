import os
import sqlite3

# Try importing pymysql for AWS RDS MySQL; fallback to sqlite3 if not installed or unreachable locally
try:
    import pymysql
    from pymysql.cursors import DictCursor
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

# AWS RDS Configuration
DB_HOST = os.getenv("DB_HOST", "database-1.c5k2wsog2wjy.ap-south-1.rds.amazonaws.com")
DB_NAME = os.getenv("DB_NAME", "zomatodb")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "J84k3I10vS5mqA7LNXz7")
DB_PORT = int(os.getenv("DB_PORT", 3306))

LOCAL_SQLITE_FILE = os.path.join(os.path.dirname(__file__), "zomato.db")

# Flag to record which database is active
IS_MYSQL = False

def get_connection():
    """Returns MySQL connection if available and reachable; otherwise returns SQLite connection for local testing."""
    global IS_MYSQL
    if HAS_PYMYSQL and os.getenv("USE_SQLITE", "").lower() not in ("true", "1", "yes"):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                port=DB_PORT,
                cursorclass=DictCursor,
                autocommit=True,
                connect_timeout=3
            )
            IS_MYSQL = True
            return conn
        except Exception:
            pass  # Fall back to SQLite locally

    IS_MYSQL = False
    conn = sqlite3.connect(LOCAL_SQLITE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Ensure database schema and default seed data exist for all roles (admin, employee, user)."""
    global IS_MYSQL

    # Test MySQL connection
    if HAS_PYMYSQL and os.getenv("USE_SQLITE", "").lower() not in ("true", "1", "yes"):
        try:
            server_conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT,
                autocommit=True,
                connect_timeout=3
            )
            with server_conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
            server_conn.close()
            IS_MYSQL = True
        except Exception:
            IS_MYSQL = False

    conn = get_connection()
    cursor = conn.cursor()

    if IS_MYSQL:
        # MySQL Syntax
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                rating DECIMAL(3, 1) NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                restaurant_name VARCHAR(100) NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                quantity INT NOT NULL,
                total_price DECIMAL(10, 2) NOT NULL,
                address TEXT NOT NULL,
                status VARCHAR(30) DEFAULT 'PLACED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Default users for 3 roles: admin, employee, customer
        cursor.execute("SELECT COUNT(*) AS total FROM users;")
        if cursor.fetchone()["total"] == 0:
            cursor.execute("""
                INSERT INTO users (username, password, role) VALUES 
                ('admin', 'admin123', 'admin'),
                ('employee', 'emp123', 'employee'),
                ('user', 'user123', 'user');
            """)

        # Default menu
        cursor.execute("SELECT COUNT(*) AS total FROM restaurants;")
        if cursor.fetchone()["total"] == 0:
            cursor.executemany(
                "INSERT INTO restaurants (name, item_name, price, rating) VALUES (%s, %s, %s, %s);",
                [
                    ("Bawarchi Biryani", "Hyderabadi Chicken Biryani", 250.0, 4.5),
                    ("Bawarchi Biryani", "Paneer Dum Biryani", 200.0, 4.3),
                    ("Pizza Corner", "Farmhouse Cheese Pizza", 300.0, 4.4),
                    ("Pizza Corner", "Garlic Breadsticks", 120.0, 4.2),
                    ("Burger King", "Crispy Veg Whopper Burger", 150.0, 4.2),
                    ("Burger King", "Chicken Whopper Burger", 190.0, 4.3)
                ]
            )
        print("[OK] [Database Tier] Connected to AWS RDS MySQL successfully!")

    else:
        # SQLite Syntax (For seamless local testing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                item_name TEXT NOT NULL,
                price REAL NOT NULL,
                rating REAL NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                restaurant_name TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                address TEXT NOT NULL,
                status TEXT DEFAULT 'PLACED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("SELECT COUNT(*) FROM users;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?);",
                [
                    ("admin", "admin123", "admin"),
                    ("employee", "emp123", "employee"),
                    ("user", "user123", "user")
                ]
            )

        cursor.execute("SELECT COUNT(*) FROM restaurants;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO restaurants (name, item_name, price, rating) VALUES (?, ?, ?, ?)",
                [
                    ("Bawarchi Biryani", "Hyderabadi Chicken Biryani", 250.0, 4.5),
                    ("Bawarchi Biryani", "Paneer Dum Biryani", 200.0, 4.3),
                    ("Pizza Corner", "Farmhouse Cheese Pizza", 300.0, 4.4),
                    ("Pizza Corner", "Garlic Breadsticks", 120.0, 4.2),
                    ("Burger King", "Crispy Veg Whopper Burger", 150.0, 4.2),
                    ("Burger King", "Chicken Whopper Burger", 190.0, 4.3)
                ]
            )
        conn.commit()
        print("[OK] [Database Tier] Connected to Local SQLite database successfully (Local Mode)!")

    conn.close()

# ----------------- User Authentication -----------------
def check_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    cursor.execute(f"SELECT * FROM users WHERE username = {ph} AND password = {ph};", (username, password))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)

def register_user(username, password, role="user"):
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    try:
        cursor.execute(f"INSERT INTO users (username, password, role) VALUES ({ph}, {ph}, {ph});", (username, password, role))
        if not IS_MYSQL:
            conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

# ----------------- Restaurant & Food Items -----------------
def get_all_restaurants():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants ORDER BY id ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_restaurant_item(name, item_name, price, rating):
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    cursor.execute(
        f"INSERT INTO restaurants (name, item_name, price, rating) VALUES ({ph}, {ph}, {ph}, {ph});",
        (name, item_name, price, rating)
    )
    if not IS_MYSQL:
        conn.commit()
    conn.close()

def update_restaurant_item(item_id, name, item_name, price, rating):
    """Allows Admin & Employee to fix/change food prices, names, and ratings."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    cursor.execute(
        f"UPDATE restaurants SET name = {ph}, item_name = {ph}, price = {ph}, rating = {ph} WHERE id = {ph};",
        (name, item_name, price, rating, item_id)
    )
    if not IS_MYSQL:
        conn.commit()
    conn.close()

def delete_restaurant_item(item_id):
    """Allows Admin to remove an item from the menu."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    cursor.execute(f"DELETE FROM restaurants WHERE id = {ph};", (item_id,))
    if not IS_MYSQL:
        conn.commit()
    conn.close()

# ----------------- Order Management -----------------
def save_order(customer_name, restaurant_name, item_name, quantity, total_price, address):
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    cursor.execute(
        f"""
        INSERT INTO orders (customer_name, restaurant_name, item_name, quantity, total_price, address)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph});
        """,
        (customer_name, restaurant_name, item_name, quantity, total_price, address)
    )
    order_id = cursor.lastrowid
    if not IS_MYSQL:
        conn.commit()
    conn.close()
    return order_id

def get_all_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_orders_by_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    cursor.execute(f"SELECT * FROM orders WHERE customer_name = {ph} ORDER BY id DESC;", (username,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_order_status(order_id, status):
    """Allows Admin & Employee to advance order status (PLACED -> PREPARING -> DELIVERED)."""
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if IS_MYSQL else "?"
    cursor.execute(f"UPDATE orders SET status = {ph} WHERE id = {ph};", (status, order_id))
    if not IS_MYSQL:
        conn.commit()
    conn.close()
