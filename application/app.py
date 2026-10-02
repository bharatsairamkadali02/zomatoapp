"""
Tier 2 — Application Server (Flask REST API)
============================================
Runs on the App Server EC2 instance (Port 5000).
Handles all business logic and exposes REST API endpoints.
Static web files are NOT served here — that is Tier 1's job (Nginx).

Environment Variables:
    ALLOWED_ORIGIN  : URL of Tier 1 Web Server (e.g. http://13.235.100.100)
                      Defaults to '*' for local development only.
                      Set this explicitly in production!
"""
import os
import sys
from flask import Flask, request, jsonify, session
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import (
    init_db,
    check_user,
    register_user,
    get_all_restaurants,
    add_restaurant_item,
    update_restaurant_item,
    delete_restaurant_item,
    save_order,
    get_all_orders,
    get_orders_by_user,
    update_order_status
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zomato_super_secret_key_123")

# ---------------------------------------------------------------------------
# CORS — Allow Tier 1 Web Server to make cross-origin API calls.
#         supports_credentials=True is required for Flask sessions to work
#         across separate machines.
#
#  PRODUCTION: Set ALLOWED_ORIGIN env var to your Tier 1 EC2 IP/domain.
#              e.g. export ALLOWED_ORIGIN=http://13.235.100.100
# ---------------------------------------------------------------------------
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
CORS(
    app,
    supports_credentials=True,
    origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else "*",
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)

# ---------------------------------------------------------------------------
# Authentication REST APIs
# ---------------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = check_user(username, password)
    if user:
        session["user"] = {"id": user["id"], "username": user["username"], "role": user["role"]}
        return jsonify({"message": "Login successful", "user": session["user"]})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "user").strip()

    # Allowed roles for public signup: user (Customer), admin (Admin)
    # Employee accounts cannot be created via public signup
    if role not in ("user", "admin"):
        role = "user"

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if register_user(username, password, role):
        return jsonify({"message": f"Account created as {role.capitalize()}! Please log in."}), 201
    return jsonify({"error": "Username already exists. Please choose another."}), 400

@app.route("/api/me", methods=["GET"])
def current_user():
    user = session.get("user")
    return jsonify(user)

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"})

# ---------------------------------------------------------------------------
# Restaurant & Menu APIs (Admin & Employee)
# ---------------------------------------------------------------------------
@app.route("/api/restaurants", methods=["GET"])
def get_restaurants():
    items = get_all_restaurants()
    return jsonify(items)

@app.route("/api/admin/restaurants", methods=["POST"])
def add_item():
    """Admin adds new restaurants & food items."""
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Admin access required to add new items"}), 403

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    item_name = data.get("item_name", "").strip()
    price = float(data.get("price", 0))
    rating = float(data.get("rating", 4.0))

    if not name or not item_name or price <= 0:
        return jsonify({"error": "Invalid restaurant or dish data"}), 400

    add_restaurant_item(name, item_name, price, rating)
    return jsonify({"message": f"Item '{item_name}' added to menu successfully!"}), 201

@app.route("/api/restaurants/<int:item_id>", methods=["PUT"])
def edit_item(item_id):
    """Admin & Employee can fix/update food prices and details."""
    user = session.get("user")
    if not user or user.get("role") not in ("admin", "employee"):
        return jsonify({"error": "Employee or Admin access required to update food prices"}), 403

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    item_name = data.get("item_name", "").strip()
    price = float(data.get("price", 0))
    rating = float(data.get("rating", 4.0))

    if not name or not item_name or price <= 0:
        return jsonify({"error": "Invalid price or item information"}), 400

    update_restaurant_item(item_id, name, item_name, price, rating)
    return jsonify({"message": f"Price & details for '{item_name}' updated successfully!"})

@app.route("/api/restaurants/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Admin only can delete an item from the menu."""
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Admin access required to delete items"}), 403

    delete_restaurant_item(item_id)
    return jsonify({"message": "Menu item deleted successfully!"})

# ---------------------------------------------------------------------------
# Order Management APIs (Customer, Employee, Admin)
# ---------------------------------------------------------------------------
@app.route("/api/order", methods=["POST"])
def place_order():
    """Customer places an order."""
    user = session.get("user")
    data = request.get_json() or {}

    customer_name = (user.get("username") if user else data.get("customer_name", "")).strip()
    restaurant_name = data.get("restaurant_name", "").strip()
    item_name = data.get("item_name", "").strip()
    price = float(data.get("price", 0))
    quantity = int(data.get("quantity", 1))
    address = data.get("address", "").strip()

    if not customer_name or not address or quantity < 1:
        return jsonify({"error": "Please provide delivery address"}), 400

    # Business Calculation: Subtotal + Flat Delivery (Rs 30)
    subtotal = price * quantity
    delivery_fee = 30.0
    total_price = subtotal + delivery_fee

    order_id = save_order(customer_name, restaurant_name, item_name, quantity, total_price, address)
    return jsonify({
        "message": "Order placed successfully!",
        "order_id": order_id,
        "total_price": total_price
    }), 201

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """
    - Admin & Employee see ALL customer orders across the platform.
    - Customer sees ONLY their own orders.
    """
    user = session.get("user")
    if not user:
        return jsonify([])

    if user.get("role") in ("admin", "employee"):
        orders = get_all_orders()
    else:
        orders = get_orders_by_user(user.get("username"))
    return jsonify(orders)

@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
def update_status(order_id):
    """Both Admin and Employee can update order status (PLACED -> PREPARING -> DELIVERED)."""
    user = session.get("user")
    if not user or user.get("role") not in ("admin", "employee"):
        return jsonify({"error": "Employee or Admin permissions required to update status"}), 403

    data = request.get_json() or {}
    new_status = data.get("status", "").strip()
    if not new_status:
        return jsonify({"error": "New status is required"}), 400

    update_order_status(order_id, new_status)
    return jsonify({"message": f"Order #{order_id} status updated to {new_status}!"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
