from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from inventory_crud import (
    get_all_products,
    add_product,
    update_product,
    delete_product,
    get_low_stock_products,
    send_low_stock_emails,
    create_user,
    authenticate_user,
    get_user_by_id,
)

app = Flask(__name__)
app.secret_key = "change-me-in-production"


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access only.", "error")
            return redirect(url_for("home"))
        return view_func(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_user():
    current_user = None
    if session.get("user_id"):
        try:
            current_user = get_user_by_id(session["user_id"])
        except Exception:
            current_user = None
    return {"current_user": current_user}


@app.route("/")
@login_required
def home():
    try:
        products = get_all_products()
        low_stock = get_low_stock_products()
    except Exception as e:
        products, low_stock = [], []
        flash(f"Error loading data: {e}", "error")
    return render_template("index.html", products=products, low_stock=low_stock)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "user").strip().lower()
            if role not in ("user", "admin"):
                role = "user"

            create_user(full_name=full_name, email=email, password=password, role=role)
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error creating account: {e}", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = authenticate_user(email, password)
            if not user:
                flash("Invalid email or password.", "error")
                return render_template("login.html")

            session["user_id"] = user["user_id"]
            session["role"] = user["role"]
            session["full_name"] = user["full_name"]
            flash(f"Welcome, {user['full_name']}!", "success")
            return redirect(url_for("home"))
        except Exception as e:
            flash(f"Login error: {e}", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/add", methods=["POST"])
@admin_required
def add():
    try:
        add_product(
            sku=request.form.get("sku", "").strip(),
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip(),
            initial_quantity=int(request.form.get("quantity", 0)),
            threshold_qty=int(request.form.get("threshold", 10)),
        )
        flash("Product added.", "success")
    except Exception as e:
        flash(f"Error adding product: {e}", "error")
    return redirect(url_for("home"))


@app.route("/edit/<int:product_id>", methods=["POST"])
@admin_required
def edit(product_id):
    try:
        update_product(
            product_id=product_id,
            sku=request.form.get("sku", "").strip(),
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip(),
            quantity=int(request.form.get("quantity", 0)),
            threshold_qty=int(request.form.get("threshold", 10)),
        )
        flash("Product updated.", "success")
    except Exception as e:
        flash(f"Error updating product: {e}", "error")
    return redirect(url_for("home"))


@app.route("/delete/<int:product_id>", methods=["POST"])
@admin_required
def remove(product_id):
    try:
        deleted = delete_product(product_id, force=True)
        flash(f"Deleted {deleted['sku']}.", "success")
    except Exception as e:
        flash(f"Error deleting product: {e}", "error")
    return redirect(url_for("home"))


@app.route("/send-alerts", methods=["POST"])
@admin_required
def send_alerts():
    try:
        count = send_low_stock_emails()
        flash(f"Sent {count} low-stock email(s).", "success")
    except Exception as e:
        flash(f"Error sending alerts: {e}", "error")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
