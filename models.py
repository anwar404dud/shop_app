# import sqlite3

# # Create shops table
# def init_db():
#     conn = sqlite3.connect('db.sqlite3')
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS shops (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             shop_type TEXT NOT NULL,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL,
#             contact TEXT,
#             address TEXT
#         )
#     ''')
#     conn.commit()
#     conn.close()

# # Create products table
# def create_products_table():
#     conn = sqlite3.connect('db.sqlite3')
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS products (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             shop_id INTEGER,
#             name TEXT NOT NULL,
#             price REAL,
#             offer TEXT,
#             quantity INTEGER,
#             image TEXT,
#             FOREIGN KEY (shop_id) REFERENCES shops(id)
#         )
#     ''')
#     conn.commit()
#     conn.close()

# def create_tables():
#     conn = sqlite3.connect('db.sqlite3')
#     c = conn.cursor()

#     # Shops table (already exists)
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS shops (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             shop_type TEXT,
#             email TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL,
#             contact TEXT,
#             address TEXT
#         )
#     ''')

#     # Products table (already exists)
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS products (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             shop_id INTEGER,
#             name TEXT NOT NULL,
#             price REAL,
#             offer TEXT,
#             quantity INTEGER,
#             image TEXT,
#             FOREIGN KEY(shop_id) REFERENCES shops(id)
#         )
#     ''')

#     # ✅ Customers table
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS customers (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             email TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL
#         )
#     ''')

#     # ✅ Cart table
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS cart (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             customer_id INTEGER,
#             product_id INTEGER,
#             quantity INTEGER,
#             FOREIGN KEY(customer_id) REFERENCES customers(id),
#             FOREIGN KEY(product_id) REFERENCES products(id)
#         )
#     ''')

#     conn.commit()
#     conn.close()

# # Run this file to create the database and tables
# if __name__ == '__main__':
#     init_db()
#     create_products_table()
#     create_tables()

import sqlite3

def create_tables():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()

    # ✅ Shops Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            shop_type TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            contact TEXT,
            address TEXT
        )
    ''')

    # ✅ Products Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER,
            name TEXT NOT NULL,
            price REAL,
            offer TEXT,
            quantity INTEGER,
            image TEXT,
            FOREIGN KEY (shop_id) REFERENCES shops(id)
        )
    ''')

    # ✅ Customers Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # ✅ Cart Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # ✅ Orders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            method TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            delivery_type TEXT,
            address TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    conn.commit()
    conn.close()

# Only run when executing this file directly
if __name__ == '__main__':
    create_tables()