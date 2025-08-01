from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import logging
from datetime import datetime
from models import create_tables

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')


# Create DB tables
try:
    create_tables()
    logging.info("Database tables created.")
except Exception as e:
    logging.error(f"Error creating tables: {e}")

@app.route('/')
def index():
    return render_template('index.html')

UPLOAD_FOLDER = 'static/shop_logos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/shop_logos', exist_ok=True)


@app.route('/shop/register', methods=['GET', 'POST'])
def shop_register():
    if request.method == 'POST':
        try:
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

        except Exception as e:
            logging.error(f"Error in shop registration: {e}")
            flash("Error occurred while registering shop.", "danger")

    return render_template('shop_register.html')


# ✅ Shop Login
@app.route('/shop/login', methods=['GET', 'POST'])
def shop_login():
    if request.method == 'POST':
        try:
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
        
        except Exception as e:
            logging.error(f"Error in shop login: {e}")
            flash("Login error.", "danger")
        

    return render_template('shop_login.html')


@app.route('/shop/dashboard')
def shop_dashboard():
    if 'shop_id' not in session:
        return redirect(url_for('shop_login'))
    
    try:
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

    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        flash("Failed to load dashboard", "danger")
        return redirect(url_for('shop_login'))


@app.route('/shop/add-product', methods=['GET', 'POST'])
def add_product():
    if 'shop_id' not in session:
        return redirect(url_for('shop_login'))
    
    if request.method == 'POST':
        try:
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
            logging.info(f"Product added by shop {session['shop_id']}: {data['name']}")
            return redirect(url_for('shop_dashboard'))
        except Exception as e:
            logging.error(f"Error adding product: {e}")
            flash("Failed to add product.", "danger")

        return redirect(url_for('shop_dashboard'))

    return render_template('add_product.html')



@app.route('/shops', methods=['GET', 'POST'])
def view_shops():
    try:
        search = request.args.get('search', '').lower()
        shop_type_filter = request.args.get('shop_type', '')
        sort = request.args.get('sort', 'latest')
        page = int(request.args.get('page', 1))
        per_page = 5  # You can adjust how many shops to show per page
        offset = (page - 1) * per_page

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()

        # Get distinct shop types
        c.execute('SELECT DISTINCT shop_type FROM shops')
        shop_types = [row[0] for row in c.fetchall()]

        # Build base query with optional filtering
        query = 'SELECT * FROM shops'
        filters = []
        params = []

        if shop_type_filter:
            filters.append('shop_type = ?')
            params.append(shop_type_filter)

        if filters:
            query += ' WHERE ' + ' AND '.join(filters)

        if sort == 'latest':
            query += ' ORDER BY id DESC'
        elif sort == 'price_low':
            query += ' ORDER BY id ASC'  # Assuming ID represents creation order

        query += ' LIMIT ? OFFSET ?'
        params.extend([per_page, offset])

        c.execute(query, params)
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

            c.execute('SELECT * FROM products WHERE shop_id = ?', (shop[0],))
            products = c.fetchall()

            if search:
                products = [p for p in products if search in p[2].lower()]

            if products:
                shop_dict['products'] = products
                shops.append(shop_dict)

        # Total number of shops for pagination
        c.execute('SELECT COUNT(*) FROM shops')
        total_shops = c.fetchone()[0]
        total_pages = (total_shops + per_page - 1) // per_page

        conn.close()
        return render_template('view_shops.html',
                            shops=shops,
                            search=search,
                            shop_type_filter=shop_type_filter,
                            shop_types=shop_types,
                            sort=sort,
                            page=page,
                            total_pages=total_pages)

    except Exception as e:
        logging.error(f"Error loading shops: {e}")
        flash("Unable to load shops.", "danger")
        return render_template('view_shops.html', shops=[], search="", shop_types=[], shop_type_filter="")



@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            conn = sqlite3.connect('db.sqlite3')
            c = conn.cursor()
            c.execute('INSERT INTO customers (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('customer_login'))
        except sqlite3.IntegrityError:
            return "⚠️ Email already exists. Try logging in."
        except Exception as e:
            logging.error(f"Error in customer registration: {e}")
            return "❌ Registration failed."

    return render_template('customer_register.html')

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        try:
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
        except Exception as e:
            logging.error(f"Error in customer login: {e}")
            return "Login failed."

    return render_template('customer_login.html')

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'customer_id' not in session:
        flash("Please login to add items to cart.")
        return redirect(url_for('customer_login'))
    try:
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
        logging.info(f"Item added to cart: product_id={product_id}, quantity={quantity}")
        flash("✅ Item added to cart!")
    except Exception as e:
        logging.error(f"Error adding to cart: {e}")
        flash("Failed to add item to cart.")
    return redirect(url_for('view_shops'))




# ✅ View Cart Page
@app.route('/cart')
def view_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    try:
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
    except Exception as e:
        logging.error(f"Error viewing cart: {e}")
        flash("Could not load your cart.")
        return redirect(url_for('view_shops'))



@app.route('/orders', methods=['GET', 'POST'])
def customer_orders():
    if 'customer_id' not in session:
        flash('Please log in to view your orders.')
        return redirect(url_for('customer_login'))

    customer_id = session['customer_id']
    status_filter = request.args.get('status', 'all')
    sort = request.args.get('sort', 'latest')
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    base_query = '''
        SELECT o.id AS order_id, p.name AS product_name, p.image,
               o.quantity, o.price, o.quantity * o.price AS total,
               o.delivery_type, o.created_at, o.status
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.customer_id = ?
    '''

    if status_filter != 'all':
        base_query += f" AND o.status = '{status_filter}'"

    if sort == 'price_asc':
        base_query += ' ORDER BY o.price ASC'
    elif sort == 'price_desc':
        base_query += ' ORDER BY o.price DESC'
    else:
        base_query += ' ORDER BY o.created_at DESC'

    base_query += ' LIMIT ? OFFSET ?'
    orders = c.execute(base_query, (customer_id, per_page, offset)).fetchall()

    total_orders = c.execute(
        f'SELECT COUNT(*) FROM orders WHERE customer_id = ?' +
        (f" AND status = '{status_filter}'" if status_filter != 'all' else ''),
        (customer_id,)
    ).fetchone()[0]

    conn.close()

    return render_template('customer_orders.html', orders=orders,
                           status_filter=status_filter, sort=sort,
                           page=page, total_pages=(total_orders + per_page - 1) // per_page)



@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'customer_id' not in session:
        flash("Login required", "danger")
        return redirect(url_for('customer_login'))

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("UPDATE orders SET status = 'Cancelled' WHERE id = ? AND customer_id = ? AND status = 'Pending'",
              (order_id, session['customer_id']))
    conn.commit()
    conn.close()
    flash("Order cancelled successfully!", "info")
    return redirect(url_for('customer_orders'))


@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    order_id = request.form['order_id']
    rating = request.form['rating']
    comment = request.form['comment']

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('UPDATE orders SET rating = ?, comment = ? WHERE id = ?',
              (rating, comment, order_id))
    conn.commit()
    conn.close()

    flash("Feedback submitted.")
    return redirect(url_for('customer_orders'))




# ✅ View Cart
@app.route('/cart')
def show_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    try:
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
        logging.info(f"Cart viewed by customer ID {session['customer_id']}, {len(cart_items)} item(s) found.")
        return render_template('cart.html', cart_items=cart_items)

    except Exception as e:
        logging.error(f"Error viewing cart for customer ID {session.get('customer_id')}: {e}")
        flash("Something went wrong while loading your cart.", "danger")
        return redirect(url_for('index'))


@app.route('/cart/update/<int:cart_id>', methods=['POST'])
def update_cart(cart_id):
    try:
        quantity = int(request.form['quantity'])

        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()

        # Get product_id from cart
        c.execute('SELECT product_id FROM cart WHERE id = ?', (cart_id,))
        result = c.fetchone()

        if result:
            product_id = result[0]

            # Correct: Check quantity (not stock)
            c.execute('SELECT quantity FROM products WHERE id = ?', (product_id,))
            stock_result = c.fetchone()
            max_stock = stock_result[0] if stock_result else 0

            if quantity > max_stock:
                flash(f"Only {max_stock} items in stock!", "warning")
                logging.warning(f"Attempt to update cart {cart_id} with quantity {quantity} > stock {max_stock}")
                conn.close()
                return redirect(url_for('show_cart'))

            # Update cart quantity
            c.execute('UPDATE cart SET quantity = ? WHERE id = ?', (quantity, cart_id))
            conn.commit()
            flash("Cart updated successfully!", "success")
            logging.info(f"Cart ID {cart_id} updated to quantity {quantity}")

        conn.close()
        return redirect(url_for('show_cart'))

    except Exception as e:
        logging.error(f"Error updating cart ID {cart_id}: {e}")
        flash("Failed to update cart item.", "danger")
        return redirect(url_for('show_cart'))




@app.route('/cart/remove/<int:cart_id>', methods=['POST'])
def remove_cart(cart_id):
    try:
        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        c.execute('DELETE FROM cart WHERE id = ?', (cart_id,))
        conn.commit()
        conn.close()
        flash("Item removed from cart.", "success")
        logging.info(f"Cart item ID {cart_id} removed")
        return redirect(url_for('show_cart'))

    except Exception as e:
        logging.error(f"Error removing cart ID {cart_id}: {e}")
        flash("Failed to remove item from cart.", "danger")
        return redirect(url_for('show_cart'))



@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'customer_id' not in session:
        flash('Please log in to checkout.')
        return redirect(url_for('customer_login'))

    try:
        customer_id = session['customer_id']
        conn = sqlite3.connect('db.sqlite3')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # ✅ Also select c.product_id for correct mapping
        cart_items = conn.execute('''
            SELECT c.id AS cart_id, c.product_id, p.name, p.price, c.quantity, p.image
            FROM cart c 
            JOIN products p ON c.product_id = p.id
            WHERE c.customer_id = ?
        ''', (customer_id,)).fetchall()

        subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart_items)
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
                    # ✅ Correct product_id used
                    conn.execute('''
                        INSERT INTO orders (customer_id, product_id, quantity, price,
                                            delivery_type, pincode, city, district, state,
                                            address, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
                    ''', (
                        customer_id, item['product_id'], item['quantity'], item['price'],
                        delivery_type, pincode, city, district, state,
                        address, order_date
                    ))
                    

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

    except Exception as e:
        logging.error(f"Checkout error for customer {session.get('customer_id')}: {e}")
        flash("Checkout failed. Please try again later.", "danger")
        return redirect(url_for('show_cart'))




@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'shop_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('shop_login'))

    try:
        conn = sqlite3.connect('db.sqlite3')
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
            flash('Product updated successfully.', 'success')
            logging.info(f"Product {product_id} updated by shop {session['shop_id']}")
            return redirect(url_for('shop_dashboard'))

        # GET request
        cur.execute("SELECT * FROM products WHERE id=? AND shop_id=?", (product_id, session['shop_id']))
        product = cur.fetchone()
        conn.close()

        if not product:
            flash('Product not found or unauthorized access.', 'danger')
            logging.warning(f"Unauthorized edit access attempt to product {product_id}")
            return redirect(url_for('shop_dashboard'))

        return render_template('edit_product.html', product=product)

    except Exception as e:
        logging.error(f"Error editing product {product_id}: {e}")
        flash("An error occurred while editing the product.", 'danger')
        return redirect(url_for('shop_dashboard'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'shop_id' not in session:
        flash('Please login to continue.', 'warning')
        return redirect(url_for('shop_login'))

    try:
        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()

        # Ensure only the shop that owns the product can delete it
        cur.execute("SELECT id FROM products WHERE id = ? AND shop_id = ?", (product_id, session['shop_id']))
        product = cur.fetchone()
        if not product:
            flash("Unauthorized or non-existent product.", "danger")
            logging.warning(f"Shop {session['shop_id']} tried to delete unauthorized product {product_id}")
            conn.close()
            return redirect(url_for('shop_dashboard'))

        cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
        flash("Product deleted successfully.", "success")
        logging.info(f"Product {product_id} deleted by shop {session['shop_id']}")
        return redirect(url_for('shop_dashboard'))

    except Exception as e:
        logging.error(f"Error deleting product {product_id}: {e}")
        flash("An error occurred while deleting the product.", "danger")
        return redirect(url_for('shop_dashboard'))


@app.route('/send_reset_link', methods=['POST'])
def send_reset_link():
    email = request.form['reset_email']
    flash(f"Password reset link sent to {email} (simulated).")
    logging.info(f"Sent simulated reset link to {email}")
    return redirect(url_for('customer_login'))

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    otp_email = request.form['otp_email']
    otp_code = request.form['otp_code']
    if otp_code == '123456':
        flash(f"OTP Verified for {otp_email} (simulated login).")
        logging.info(f"OTP verified for {otp_email}")
    else:
        flash("Invalid OTP. Please try again.")
        logging.warning(f"Invalid OTP attempt for {otp_email}")
    return redirect(url_for('customer_login'))

@app.route('/remove_order/<int:order_id>', methods=['POST'])
def remove_order(order_id):
    try:
        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()

        # Optional: verify customer ownership before deletion (if needed)
        c.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        conn.commit()
        conn.close()

        flash('Order removed successfully.', 'success')
        logging.info(f"Order ID {order_id} removed by customer")
    except Exception as e:
        logging.error(f"Error removing order ID {order_id}: {e}")
        flash("Error removing order.", "danger")
    return redirect(url_for('customer_orders'))

@app.context_processor
def inject_user_data():
    def get_cart_count():
        try:
            cart = session.get('cart', {})
            return sum(cart.values())
        except Exception as e:
            logging.warning(f"Failed to count cart items: {e}")
            return 0
    return dict(get_cart_count=get_cart_count, current_user=session.get('user'))


@app.route('/customer/logout')
def customer_logout():
    session.pop('customer_id', None)
    session.pop('cart_count', None)
    logging.info("Customer logged out.")
    return redirect(url_for('index'))

@app.route('/shop/logout')
def shop_logout():
    session.pop('shop_id', None)
    session.pop('shop_name', None)
    logging.info("Shop logged out.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    logging.info("App started.")
    app.run(debug=True)
