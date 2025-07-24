# from flask import Flask, render_template, request, redirect, url_for, session
# import os

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # Replace with a secure key
# app.config['UPLOAD_FOLDER'] = 'uploads'

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/shop/login')
# def shop_login():
#     return render_template('shop_login.html')

# @app.route('/shop/register')
# def shop_register():
#     return render_template('shop_register.html')

# @app.route('/shop/dashboard')
# def shop_dashboard():
#     # Add login check logic here
#     return render_template('shop_dashboard.html')

# @app.route('/shop/add-product')
# def add_product():
#     return render_template('add_product.html')

# if __name__ == '__main__':
#     if not os.path.exists('uploads'):
#         os.makedirs('uploads')
#     app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, flash
# from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
from models import create_tables
create_tables()
import os

app = Flask(__name__)
app.secret_key = '0d6e8e0841fcd6495e8d83e01c7725ec'  # Change to a strong random key
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# ✅ Home Page
@app.route('/')
def index():
    return render_template('index.html')

# ✅ Shop Registration
# @app.route('/shop/register', methods=['GET', 'POST'])
# def shop_register():
#     if request.method == 'POST':
#         name = request.form['name']
#         shop_type = request.form['shop_type']
#         username = request.form['username']
#         password = request.form['password']
#         contact = request.form['contact']
#         address = request.form['address']

#         conn = sqlite3.connect('db.sqlite3')
#         c = conn.cursor()
#         try:
#             c.execute('INSERT INTO shops (name, shop_type, username, password, contact, address) VALUES (?, ?, ?, ?, ?, ?)',
#                       (name, shop_type, username, password, contact, address))
#             conn.commit()
#         except sqlite3.IntegrityError:
#             return "⚠️ Username already exists. Try a different one."
#         conn.close()
#         return redirect(url_for('shop_login'))

#     return render_template('shop_register.html')

UPLOAD_FOLDER = 'static/shop_logos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/shop/register', methods=['GET', 'POST'])
def shop_register():
    if request.method == 'POST':
        name = request.form['name']
        shop_type = request.form['shop_type']
        username = request.form['username']
        password = request.form['password']
        contact = request.form['contact']
        address = request.form['address']
        logo = request.files.get('logo')  # Can be None

        logo_filename = None
        if logo and logo.filename:
            logo_filename = secure_filename(logo.filename)
            logo.save(os.path.join(UPLOAD_FOLDER, logo_filename))

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO shops (name, shop_type, username, password, contact, address, logo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, shop_type, username, password, contact, address, logo_filename))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("⚠️ Username already exists. Try a different one.", "danger")
            return redirect(url_for('shop_register'))

        conn.close()
        flash("✅ Shop registered successfully!", "success")
        return redirect(url_for('shop_login'))

    return render_template('shop_register.html')

# ✅ Shop Login
@app.route('/shop/login', methods=['GET', 'POST'])
def shop_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        c.execute('SELECT * FROM shops WHERE username=? AND password=?', (username, password))
        shop = c.fetchone()
        conn.close()

        if shop:
            session['shop_id'] = shop[0]
            session['shop_name'] = shop[1]
            return redirect(url_for('shop_dashboard'))
        else:
            return "❌ Invalid credentials. Please try again."

    return render_template('shop_login.html')

# ✅ Shop Dashboard (protected)
# @app.route('/shop/dashboard')
# def shop_dashboard():
#     if 'shop_id' not in session:
#         return redirect(url_for('shop_login'))
#     conn = sqlite3.connect('db.sqlite3')
#     c = conn.cursor()
#     c.execute('SELECT * FROM products WHERE shop_id = ?', (session['shop_id'],))
#     products = c.fetchall()
#     conn.close()

#     return render_template('shop_dashboard.html', shop_name=session['shop_name'], products=products)
    # return render_template('shop_dashboard.html', shop_name=session['shop_name'])

@app.route('/shop/dashboard')
def shop_dashboard():
    if 'shop_id' not in session:
        return redirect(url_for('shop_login'))

    shop_id = session['shop_id']
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()

    cur.execute("SELECT name, logo FROM shops WHERE id = ?", (shop_id,))
    shop_data = cur.fetchone()

    cur.execute("SELECT * FROM products WHERE shop_id = ?", (shop_id,))
    products = cur.fetchall()

    conn.close()

    return render_template('shop_dashboard.html',
                           shop_name=shop_data[0],
                           shop_logo=shop_data[1],
                           products=products)


@app.route('/shop/add-product', methods=['GET', 'POST'])
def add_product():
    if 'shop_id' not in session:
        return redirect(url_for('shop_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        offer = request.form.get('offer') or 0  # defaults to 0 if not filled
        quantity = request.form['quantity']
        image = request.files['image']

        image_filename = ''
        if image and image.filename != '':
            image_filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        c.execute('''
            INSERT INTO products (shop_id, name, price, offer, quantity, image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['shop_id'], name, price, offer, quantity, image_filename))
        conn.commit()
        conn.close()

        return redirect(url_for('shop_dashboard'))

    return render_template('add_product.html')

@app.route('/shops', methods=['GET', 'POST'])
def view_shops():
    search = request.args.get('search', '').lower()
    shop_type_filter = request.args.get('shop_type', '')

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()

    # Get distinct shop types
    c.execute('SELECT DISTINCT shop_type FROM shops')
    shop_types = [row[0] for row in c.fetchall()]

    # Get all shops
    c.execute('SELECT * FROM shops')
    shops_data = c.fetchall()

    shops = []
    for shop in shops_data:
        shop_dict = {
            'id': shop[0],
            'name': shop[1],
            'shop_type': shop[2],
            'contact': shop[5],
            'address': shop[6],
            'logo': shop[7],
            'products': []
        }

        # Filter by shop_type if applied
        if shop_type_filter and shop_dict['shop_type'].lower() != shop_type_filter.lower():
            continue

        c.execute('SELECT * FROM products WHERE shop_id = ?', (shop[0],))
        products = c.fetchall()

        if search:
            products = [p for p in products if search in p[2].lower()]

        if products:
            shop_dict['products'] = products
            shops.append(shop_dict)

    conn.close()
    return render_template('view_shops.html',
                           shops=shops,
                           search=search,
                           shop_type_filter=shop_type_filter,
                           shop_types=shop_types)


@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO customers (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('customer_login'))
        except sqlite3.IntegrityError:
            return "⚠️ Email already exists. Try logging in."

    return render_template('customer_register.html')

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        c.execute('SELECT * FROM customers WHERE email=? AND password=?', (email, password))
        customer = c.fetchone()
        conn.close()

        if customer:
            session['customer_id'] = customer[0]
            session['customer_name'] = customer[1]
            return redirect(url_for('view_shops'))  # or a separate dashboard if needed
        else:
            return "❌ Invalid email or password"

    return render_template('customer_login.html')

# ✅ Add product to cart
# @app.route('/add-to-cart/<int:product_id>', methods=['POST'])
# def add_to_cart(product_id):
#     if 'customer_id' not in session:
#         return redirect(url_for('customer_login'))

#     customer_id = session['customer_id']

#     conn = sqlite3.connect('db.sqlite3')
#     c = conn.cursor()

#     # Check if item already in cart
#     c.execute('SELECT * FROM cart WHERE customer_id = ? AND product_id = ?', (customer_id, product_id))
#     item = c.fetchone()

#     if item:
#         # Increase quantity by 1
#         c.execute('UPDATE cart SET quantity = quantity + 1 WHERE id = ?', (item[0],))
#     else:
#         # Insert new item with quantity = 1
#         c.execute('INSERT INTO cart (customer_id, product_id, quantity) VALUES (?, ?, ?)', (customer_id, product_id, 1))

#     conn.commit()
#     conn.close()

#     return redirect(url_for('view_shops'))  # Redirect back to shop view

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'customer_id' not in session:
        flash("Please login to add items to cart.")
        return redirect(url_for('customer_login'))

    quantity = int(request.form.get('quantity', 1))  # ✅ get quantity from form

    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()

    # Check if already in cart
    cur.execute("SELECT id, quantity FROM cart WHERE customer_id=? AND product_id=?", 
                (session['customer_id'], product_id))
    item = cur.fetchone()

    if item:
        # ✅ Update existing quantity
        new_qty = item[1] + quantity
        cur.execute("UPDATE cart SET quantity=? WHERE id=?", (new_qty, item[0]))
    else:
        cur.execute("INSERT INTO cart (customer_id, product_id, quantity) VALUES (?, ?, ?)",
                    (session['customer_id'], product_id, quantity))

    conn.commit()
    conn.close()

    flash("✅ Item added to cart!")
    return redirect(url_for('view_shops'))


# def get_db_connection():
#     conn = sqlite3.connect('db.sqlite3')
#     conn.row_factory = sqlite3.Row
#     return conn

# def get_cart_count():
#     if 'customer_id' not in session:
#         return 0
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("SELECT SUM(quantity) FROM cart WHERE customer_id=?", (session['customer_id'],))
#     result = cur.fetchone()
#     conn.close()
#     return result[0] if result[0] else 0



# ✅ View Cart Page
@app.route('/cart')
def view_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    customer_id = session['customer_id']
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()

    c.execute('''
        SELECT cart.id, products.name, products.price, cart.quantity, products.image
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.customer_id = ?
    ''', (customer_id,))
    cart_items = c.fetchall()

    # Calculate total
    total = sum(item[2] * item[3] for item in cart_items)

    # Count cart items for badge
    c.execute('SELECT COUNT(*) FROM cart WHERE customer_id = ?', (customer_id,))
    count = c.fetchone()[0]
    session['cart_count'] = count

    conn.close()
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/customer/logout')
def customer_logout():
    session.pop('customer_id', None)
    return redirect(url_for('index'))

# ✅ View Cart
@app.route('/cart')
def show_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''
        SELECT cart.id, products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.customer_id = ?
    ''', (session['customer_id'],))
    cart_items = c.fetchall()
    conn.close()

    return render_template('cart.html', cart_items=cart_items)

# ✅ Update Cart Quantity
# @app.route('/cart/update/<int:cart_id>', methods=['POST'])
# def update_cart(cart_id):
#     quantity = int(request.form['quantity'])

#     conn = sqlite3.connect('db.sqlite3')
#     c = conn.cursor()
#     c.execute('UPDATE cart SET quantity = ? WHERE id = ?', (quantity, cart_id))
#     conn.commit()
#     conn.close()

#     flash("Cart updated successfully!")
#     return redirect(url_for('show_cart'))

@app.route('/cart/update/<int:cart_id>', methods=['POST'])
def update_cart(cart_id):
    quantity = int(request.form['quantity'])

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()

    # Get product_id and stock
    c.execute('''
        SELECT product_id FROM cart WHERE id = ?
    ''', (cart_id,))
    result = c.fetchone()
    if result:
        product_id = result[0]
        c.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
        stock_result = c.fetchone()
        max_stock = stock_result[0] if stock_result else 0

        if quantity > max_stock:
            flash(f"Only {max_stock} items in stock!")
            conn.close()
            return redirect(url_for('show_cart'))

        # Update cart quantity
        c.execute('UPDATE cart SET quantity = ? WHERE id = ?', (quantity, cart_id))
        conn.commit()
    conn.close()
    flash("Cart updated successfully!")
    return redirect(url_for('show_cart'))


# ✅ Remove from Cart
@app.route('/cart/remove/<int:cart_id>', methods=['POST'])
def remove_cart(cart_id):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('DELETE FROM cart WHERE id = ?', (cart_id,))
    conn.commit()
    conn.close()

    flash("Item removed from cart.")
    return redirect(url_for('show_cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'customer_id' not in session:
        flash('Please log in to checkout.')
        return redirect(url_for('customer_login'))

    # customer_id = session['customer_id']
    # conn = get_db_connection()
    customer_id = session['customer_id']
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row  # ✅ enables dict-like access
    c = conn.cursor()
    

    cart_items = conn.execute('''
        SELECT c.id, p.name, p.price, c.quantity, p.image
        FROM cart c JOIN products p ON c.product_id = p.id
        WHERE c.customer_id = ?
    ''', (customer_id,)).fetchall()
    print("CART ITEMS >>>", cart_items)
    subtotal = sum(float(item[2]) * int(item[3]) for item in cart_items)
    discount = 0
    discount_percent = 0
    coupon_code = request.form.get('coupon_code') or ''

    if request.method == 'POST':
        if 'apply_coupon' in request.form:
            if coupon_code.lower() == 'save10':
                discount_percent = 10
                discount = round(subtotal * 0.10, 2)
                flash('10% discount applied!')
            else:
                flash('Invalid coupon code')
            total = subtotal - discount
            return render_template('checkout.html', cart_items=cart_items,
                                   total=total, discount=discount,
                                   discount_percent=discount_percent,
                                   coupon_code=coupon_code)

        if 'place_order' in request.form:
            delivery_type = request.form.get('delivery_type')
            pincode = request.form.get('pincode')
            city = request.form.get('city')
            district = request.form.get('district')
            state = request.form.get('state')
            address = request.form.get('address')
            order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for item in cart_items:
                conn.execute('''
                    INSERT INTO orders (customer_id, product_id, quantity, price,
                                        delivery_type, pincode, city, district, state,
                                        address, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
                ''', (customer_id, item['id'], item['quantity'], item['price'],
                      delivery_type, pincode, city, district, state,
                      address, order_date))

            conn.execute('DELETE FROM cart WHERE customer_id = ?', (customer_id,))
            conn.commit()
            flash('Order placed successfully!')

            return redirect(url_for('customer_orders'))

    total = subtotal - discount
    conn.close()
    return render_template('checkout.html', cart_items=cart_items,
                           total=total, discount=discount,
                           discount_percent=discount_percent,
                           coupon_code=coupon_code)


# @app.route('/orders', methods=['GET', 'POST'])
# def customer_orders():
#     if 'customer_id' not in session:
#         flash('Please log in to view orders.')
#         return redirect(url_for('customer_login'))

#     conn = sqlite3.connect('db.sqlite3')
#     c = conn.cursor()
#     c.execute('''
#         SELECT orders.id, products.name, orders.quantity, products.price,
#             orders.method, orders.delivery_type, orders.address,
#             orders.status, orders.created_at
#         FROM orders
#         JOIN products ON orders.product_id = products.id
#         WHERE orders.customer_id = ?
#         ORDER BY orders.created_at DESC
#     ''', (session['customer_id'],))

#     orders = c.fetchall()
#     conn.close()

#     return render_template('customer_orders.html', orders=orders)

# @app.route('/orders', methods=['GET', 'POST'])
# def customer_orders():
#     if 'customer_id' not in session:
#         flash('Please log in to view orders.')
#         return redirect(url_for('customer_login'))

#     status_filter = request.args.get('status', '')

    # conn = sqlite3.connect('db.sqlite3')
    # c = conn.cursor()

#     query = '''
#         SELECT orders.id, products.name, orders.quantity, products.price,
#             orders.method, orders.delivery_type, orders.address,
#             orders.status, orders.created_at, products.image
#         FROM orders
#         JOIN products ON orders.product_id = products.id
#         WHERE orders.customer_id = ?
#     '''
#     params = [session['customer_id']]

#     if status_filter:
#         query += " AND orders.status = ?"
#         params.append(status_filter)

#     query += " ORDER BY orders.created_at DESC"

#     c.execute(query, tuple(params))
#     orders = c.fetchall()
#     conn.close()

#     return render_template('customer_orders.html', orders=orders, status_filter=status_filter)

@app.route('/orders', methods=['GET', 'POST'])
def customer_orders():
    if 'customer_id' not in session:
        flash('Please log in to view orders.')
        return redirect(url_for('customer_login'))

    status_filter = request.args.get('status', '')

    customer_id = session.get('customer_id')
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if status_filter:
        c.execute("""
            SELECT orders.id as order_id, products.name as product_name, orders.quantity,
                   products.price, orders.method as payment_method,
                   orders.delivery_type as delivery_method, orders.address,
                   orders.status, orders.created_at as order_time,
                   products.image
            FROM orders
            LEFT JOIN products ON orders.product_id = products.id
            WHERE orders.customer_id = ? AND orders.status = ?
            ORDER BY orders.created_at DESC
        """, (customer_id, status_filter))
    else:
        c.execute("""
            SELECT orders.id as order_id, products.name as product_name, orders.quantity,
                   products.price, orders.method as payment_method,
                   orders.delivery_type as delivery_method, orders.address,
                   orders.status, orders.created_at as order_time,
                   products.image
            FROM orders
            LEFT JOIN products ON orders.product_id = products.id
            WHERE orders.customer_id = ?
            ORDER BY orders.created_at DESC
        """, (customer_id,))

    rows = c.fetchall()
    conn.close()

    # Convert to dict and parse order_time
    orders = []
    for row in rows:
        order = dict(row)
        if 'order_time' in order and order['order_time']:
            try:
                order['order_time'] = datetime.strptime(order['order_time'], '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"Error parsing order_time: {e}")
                order['order_time'] = None
        orders.append(order)

    return render_template('customer_orders.html', orders=orders, status_filter=status_filter)





@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'shop_id' not in session:
        flash('Please login to continue.')
        return redirect(url_for('shop_login'))

    conn = sqlite3.connect('db.sqlite3')  # ✅ Define the connection
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        offer = request.form['offer']
        quantity = request.form['quantity']
        
        cur.execute("""
            UPDATE products SET name=?, price=?, offer=?, quantity=?
            WHERE id=? AND shop_id=?
        """, (name, price, offer, quantity, product_id, session['shop_id']))
        
        conn.commit()
        conn.close()
        flash('Product updated successfully.')
        return redirect(url_for('shop_dashboard'))

    # For GET request – fetch current product info
    cur.execute("SELECT * FROM products WHERE id=? AND shop_id=?", (product_id, session['shop_id']))
    product = cur.fetchone()
    conn.close()

    if not product:
        flash('Product not found or unauthorized access.')
        return redirect(url_for('shop_dashboard'))

    return render_template('edit_product.html', product=product)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    flash("Product deleted", "success")
    return redirect(url_for('shop_dashboard'))

@app.route('/send_reset_link', methods=['POST'])
def send_reset_link():
    email = request.form['reset_email']
    # You could add email lookup logic here
    flash(f"Password reset link sent to {email} (simulated).")
    return redirect(url_for('customer_login'))

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    otp_email = request.form['otp_email']
    otp_code = request.form['otp_code']
    # Simulated OTP check
    if otp_code == '123456':
        flash(f"OTP Verified for {otp_email} (simulated login).")
        # You could start a session here
    else:
        flash("Invalid OTP. Please try again.")
    return redirect(url_for('customer_login'))
    
@app.context_processor
def inject_user_data():
    def get_cart_count():
        cart = session.get('cart', {})
        return sum(cart.values())
    return dict(get_cart_count=get_cart_count, current_user=session.get('user'))

# google_bp = make_google_blueprint(client_id="...", client_secret="...", redirect_to="google_callback")
# app.register_blueprint(google_bp, url_prefix="/login")

# @app.route("/google-callback")
# def google_callback():
#     resp = google.get("/oauth2/v2/userinfo")
#     if not resp.ok:
#         return redirect(url_for("shop_login"))
#     user_info = resp.json()
#     # Do something with user_info
#     return redirect(url_for("shop_dashboard"))  # example

@app.route('/remove_order/<int:order_id>', methods=['POST'])
def remove_order(order_id):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()

    # Delete the order with matching ID
    cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()

    flash('Order removed successfully.', 'success')
    return redirect(url_for('customer_orders'))



# Run Flask
if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)