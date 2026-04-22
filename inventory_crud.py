import os, smtplib, psycopg2, psycopg2.extras, hashlib, hmac, base64, secrets
from email.mime.text import MIMEText
from typing import Optional, Dict, List, Any

DATABASE_URL = os.environ.get("DATABASE_URL")
ALERT_FROM_EMAIL = os.environ.get("ALERT_FROM_EMAIL", "")
ALERT_TO_EMAIL = os.environ.get("ALERT_TO_EMAIL", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"


def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set!")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 200000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}$" + base64.b64encode(salt).decode("utf-8") + "$" + base64.b64encode(derived).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_b64, derived_b64 = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected = base64.b64decode(derived_b64.encode("utf-8"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_user(full_name:str, email:str, password:str, role:str="user")->Dict[str,Any]:
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    password_hash = hash_password(password)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO inventory.app_users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id, full_name, email, role, created_at""", (full_name, email, password_hash, role))
            user = cur.fetchone()
            conn.commit()
            return user
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def authenticate_user(email:str, password:str)->Optional[Dict[str,Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, full_name, email, password_hash, role FROM inventory.app_users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user and verify_password(password, user["password_hash"]):
                return user
            return None
    finally:
        conn.close()


def get_user_by_id(user_id:int)->Optional[Dict[str,Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, full_name, email, role, created_at FROM inventory.app_users WHERE user_id = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def add_product(sku:str, name:str, description:str="", initial_quantity:int=0, threshold_qty:int=10, cooldown_hours:int=12, enabled:bool=True)->Dict[str,Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO inventory.products (sku, name, description, active) VALUES (%s, %s, %s, TRUE) RETURNING product_id, sku, name, description, created_at", (sku, name, description))
            product = cur.fetchone()
            pid = product["product_id"]
            cur.execute("INSERT INTO inventory.inventory_levels (product_id, quantity) VALUES (%s, %s)", (pid, initial_quantity))
            cur.execute("INSERT INTO inventory.product_thresholds (product_id, threshold_qty, cooldown, enabled) VALUES (%s, %s, %s * INTERVAL '1 hour', %s)", (pid, threshold_qty, cooldown_hours, enabled))
            conn.commit()
            return product
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def update_product(product_id:int, sku:str, name:str, description:str, quantity:int, threshold_qty:int)->Dict[str,Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE inventory.products SET sku=%s, name=%s, description=%s WHERE product_id=%s RETURNING product_id, sku, name, description", (sku, name, description, product_id))
            product = cur.fetchone()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            cur.execute("UPDATE inventory.inventory_levels SET quantity=%s, updated_at=CURRENT_TIMESTAMP WHERE product_id=%s", (quantity, product_id))
            cur.execute("UPDATE inventory.product_thresholds SET threshold_qty=%s WHERE product_id=%s", (threshold_qty, product_id))
            conn.commit()
            return product
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def delete_product(product_id:int, force:bool=False)->Dict[str,Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, sku, name FROM inventory.products WHERE product_id=%s", (product_id,))
            info = cur.fetchone()
            if not info:
                raise ValueError(f"Product {product_id} not found")
            if not force:
                return {"warning": "Deletion requires force=True", "product": info}
            cur.execute("DELETE FROM inventory.stock_alerts WHERE product_id=%s", (product_id,))
            cur.execute("DELETE FROM inventory.inventory_levels WHERE product_id=%s", (product_id,))
            cur.execute("DELETE FROM inventory.product_thresholds WHERE product_id=%s", (product_id,))
            cur.execute("DELETE FROM inventory.products WHERE product_id=%s RETURNING product_id, sku, name, created_at", (product_id,))
            deleted = cur.fetchone()
            conn.commit()
            return deleted
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def get_all_products()->List[Dict[str,Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT p.product_id, p.sku, p.name, p.description, p.active,
            COALESCE(il.quantity,0) as current_quantity, COALESCE(pt.threshold_qty,0) as threshold_qty,
            COALESCE(pt.enabled,FALSE) as threshold_enabled,
            CASE WHEN COALESCE(il.quantity,0) < COALESCE(pt.threshold_qty,0) AND COALESCE(pt.enabled,FALSE) THEN 'LOW STOCK' ELSE 'OK' END as stock_status
            FROM inventory.products p
            LEFT JOIN inventory.inventory_levels il ON p.product_id = il.product_id
            LEFT JOIN inventory.product_thresholds pt ON p.product_id = pt.product_id
            ORDER BY p.product_id DESC""")
            return cur.fetchall()
    finally:
        conn.close()


def get_low_stock_products()->List[Dict[str,Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT p.product_id, p.sku, p.name, il.quantity as current_quantity, pt.threshold_qty
            FROM inventory.products p
            JOIN inventory.inventory_levels il ON p.product_id = il.product_id
            JOIN inventory.product_thresholds pt ON p.product_id = pt.product_id
            WHERE il.quantity < pt.threshold_qty AND pt.enabled = TRUE
            ORDER BY il.quantity ASC, p.name ASC""")
            return cur.fetchall()
    finally:
        conn.close()


def log_low_stock_alerts()->int:
    low_stock = get_low_stock_products()
    if not low_stock:
        return 0
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for item in low_stock:
                msg = f"Low stock for {item['sku']} - {item['name']}: {item['current_quantity']} left, threshold {item['threshold_qty']}"
                cur.execute("INSERT INTO inventory.stock_alerts (product_id, alert_message) VALUES (%s, %s)", (item["product_id"], msg))
            conn.commit()
            return len(low_stock)
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def send_low_stock_emails()->int:
    low_stock = get_low_stock_products()
    if not low_stock:
        return 0
    if not all([SMTP_HOST, ALERT_FROM_EMAIL, ALERT_TO_EMAIL]):
        raise ValueError("Missing email settings. Set SMTP_HOST, ALERT_FROM_EMAIL, and ALERT_TO_EMAIL.")
    body = "Low-stock products:\n\n" + "\n".join([f"- {i['sku']} | {i['name']} | Qty: {i['current_quantity']} | Threshold: {i['threshold_qty']}" for i in low_stock])
    msg = MIMEText(body)
    msg["Subject"] = f"Inventory Alert: {len(low_stock)} low-stock product(s)"
    msg["From"] = ALERT_FROM_EMAIL
    msg["To"] = ALERT_TO_EMAIL
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(ALERT_FROM_EMAIL, [a.strip() for a in ALERT_TO_EMAIL.split(",")], msg.as_string())
    log_low_stock_alerts()
    return len(low_stock)
