from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import requests
import os
import json
import time

app = Flask(__name__)
app.secret_key = "sweet-scoop-secret-key"

DATABASE = "orders.db"

# Paystack Test Secret Key
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")

# Your local Flask website
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "http://127.0.0.1:5000")


# ============================================================
# DATABASE
# ============================================================

def create_database():
    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'Pending',
            payment_status TEXT DEFAULT 'Pending',
            payment_reference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    # Add payment columns if the database already existed
    columns = connection.execute(
        "PRAGMA table_info(orders)"
    ).fetchall()

    column_names = [column[1] for column in columns]

    if "payment_status" not in column_names:
        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN payment_status TEXT DEFAULT 'Pending'
        """)

    if "payment_reference" not in column_names:
        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN payment_reference TEXT
        """)

    connection.commit()
    connection.close()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# CUSTOMER PLACE ORDER
# ============================================================

@app.route("/place-order", methods=["POST"])
def place_order():

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    items = request.form.get("items", "").strip()
    notes = request.form.get("notes", "").strip()
    total = request.form.get("total", "0").strip()

    if not name or not phone or not address or not items:
        return "Please complete all required fields.", 400

    try:
        total = float(total)
    except ValueError:
        return "Invalid order total.", 400

    connection = sqlite3.connect(DATABASE)

    cursor = connection.execute("""
        INSERT INTO orders
        (
            customer_name,
            phone,
            address,
            items,
            total,
            notes,
            status,
            payment_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        phone,
        address,
        items,
        total,
        notes,
        "Pending",
        "Pending"
    ))

    order_id = cursor.lastrowid

    connection.commit()
    connection.close()

    # Send customer to payment
    return redirect(url_for(
        "initialize_payment",
        order_id=order_id
    ))


# ============================================================
# INITIALIZE PAYSTACK PAYMENT
# ============================================================

@app.route("/initialize-payment/<int:order_id>")
def initialize_payment(order_id):

    if not PAYSTACK_SECRET_KEY:
        return """
        <h2>Paystack is not configured yet.</h2>
        <p>Please make sure PAYSTACK_SECRET_KEY is set in the terminal.</p>
        """, 500

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    order = connection.execute("""
        SELECT *
        FROM orders
        WHERE id = ?
    """, (order_id,)).fetchone()

    connection.close()

    if not order:
        return "Order not found.", 404

    # Paystack requires amount in pesewas for Ghana
    amount_in_pesewas = int(round(order["total"] * 100))

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "email": "customer@sweetscoop.com",
        "amount": amount_in_pesewas,
        "currency": "GHS",
       "reference": f"sweetscoop-{order_id}-{int(time.time())}",
        "callback_url": f"{BASE_URL}/payment/callback"
    }

    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers=headers,
            json=data,
            timeout=30
        )

        result = response.json()

    except Exception as error:
        return f"""
        <h2>Payment connection error</h2>
        <p>{error}</p>
        """, 500

    if not result.get("status"):
        return f"""
        <h2>Unable to initialize payment</h2>
        <p>{result.get("message", "Unknown Paystack error")}</p>
        """, 500

    authorization_url = result["data"]["authorization_url"]

    return redirect(authorization_url)


# ============================================================
# PAYSTACK CALLBACK
# ============================================================

@app.route("/payment/callback")
def payment_callback():

    reference = request.args.get("reference")

    if not reference:
        return "Payment reference was not provided.", 400

    return redirect(url_for(
        "verify_payment",
        reference=reference
    ))


# ============================================================
# VERIFY PAYSTACK PAYMENT
# ============================================================

@app.route("/payment/verify/<reference>")
def verify_payment(reference):

    if not PAYSTACK_SECRET_KEY:
        return "Paystack secret key is not configured.", 500

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }

    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=30
        )

        result = response.json()

    except Exception as error:
        return f"""
        <h2>Payment verification error</h2>
        <p>{error}</p>
        """, 500

    if not result.get("status"):
        return f"""
        <h2>Payment verification failed</h2>
        <p>{result.get("message", "Unknown error")}</p>
        """, 400

    transaction = result.get("data", {})

    payment_status = transaction.get("status")
    amount = transaction.get("amount", 0)
    reference_from_paystack = transaction.get("reference")

    if payment_status == "success":

        order_id = None

        try:
            if reference.startswith("sweetscoop-order-"):
                order_id = int(
                    reference.replace("sweetscoop-order-", "")
                )
        except ValueError:
            pass

        if order_id:

            connection = sqlite3.connect(DATABASE)

            connection.execute("""
                UPDATE orders
                SET payment_status = 'Paid',
                    payment_reference = ?
                WHERE id = ?
            """, (
                reference_from_paystack,
                order_id
            ))

            connection.commit()
            connection.close()

        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Payment Successful</title>
        </head>

        <body style="font-family: Arial; text-align: center; padding: 50px;">

            <h1>🍦 Sweet Scoop</h1>

            <h2>✅ Payment Successful!</h2>

            <p>Thank you for your order.</p>

            <p>Your payment has been confirmed.</p>

            <p>We will begin processing your order.</p>

            <br>

            <a href="/">
                Return to Sweet Scoop
            </a>

        </body>
        </html>
        """

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Not Completed</title>
    </head>

    <body style="font-family: Arial; text-align: center; padding: 50px;">

        <h1>🍦 Sweet Scoop</h1>

        <h2>❌ Payment was not completed</h2>

        <p>Your order has not been marked as paid.</p>

        <br>

        <a href="/">
            Return to Sweet Scoop
        </a>

    </body>
    </html>
    """, 400


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "admin" and password == "admin123":

            session["admin_logged_in"] = True

            return redirect(url_for("admin"))

        return render_template(
            "login.html",
            error="Incorrect username or password."
        )

    return render_template("login.html")


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    orders = connection.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """).fetchall()

    total_orders = connection.execute("""
        SELECT COUNT(*)
        FROM orders
    """).fetchone()[0]

    pending_orders = connection.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'Pending'
    """).fetchone()[0]

    delivered_orders = connection.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'Delivered'
    """).fetchone()[0]

    connection.close()

    return render_template(
        "admin.html",
        orders=orders,
        total_orders=total_orders,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders
    )


# ============================================================
# MARK ORDER AS DELIVERED
# ============================================================

@app.route("/admin/deliver/<int:order_id>", methods=["POST"])
def deliver_order(order_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        UPDATE orders
        SET status = 'Delivered'
        WHERE id = ?
    """, (order_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("admin"))


# ============================================================
# DELETE ORDER
# ============================================================

@app.route("/admin/delete/<int:order_id>", methods=["POST"])
def delete_order(order_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        DELETE FROM orders
        WHERE id = ?
    """, (order_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("admin"))


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("login"))


# ============================================================
# PAYSTACK WEBHOOK
# ============================================================

@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():

    # We will add signature verification here
    # when we configure the Paystack webhook URL.

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": "ignored"}), 200

    event = data.get("event")

    if event == "charge.success":

        transaction = data.get("data", {})

        reference = transaction.get("reference")

        if reference:

            order_id = None

            try:
                if reference.startswith("sweetscoop-order-"):
                    order_id = int(
                        reference.replace(
                            "sweetscoop-order-", ""
                        )
                    )
            except ValueError:
                pass

            if order_id:

                connection = sqlite3.connect(DATABASE)

                connection.execute("""
                    UPDATE orders
                    SET payment_status = 'Paid',
                        payment_reference = ?
                    WHERE id = ?
                """, (
                    reference,
                    order_id
                ))

                connection.commit()
                connection.close()

    return jsonify({"status": "success"}), 200


# ============================================================
# START FLASK
# ============================================================

create_database()

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )