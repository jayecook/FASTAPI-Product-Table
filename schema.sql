CREATE SCHEMA IF NOT EXISTS inventory;

CREATE TABLE IF NOT EXISTS inventory.app_users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory.products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory.inventory_levels (
    product_id INTEGER PRIMARY KEY REFERENCES inventory.products(product_id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory.product_thresholds (
    product_id INTEGER PRIMARY KEY REFERENCES inventory.products(product_id) ON DELETE CASCADE,
    threshold_qty INTEGER NOT NULL DEFAULT 10,
    cooldown INTERVAL DEFAULT INTERVAL '12 hours',
    enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS inventory.stock_alerts (
    alert_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES inventory.products(product_id) ON DELETE CASCADE,
    alert_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);

CREATE OR REPLACE VIEW inventory.v_open_stock_alerts AS
SELECT sa.alert_id, sa.product_id, p.sku, p.name, il.quantity, pt.threshold_qty, sa.alert_message, sa.created_at, sa.resolved_at
FROM inventory.stock_alerts sa
JOIN inventory.products p ON sa.product_id = p.product_id
LEFT JOIN inventory.inventory_levels il ON p.product_id = il.product_id
LEFT JOIN inventory.product_thresholds pt ON p.product_id = pt.product_id
WHERE sa.resolved_at IS NULL;

INSERT INTO inventory.app_users (full_name, email, password_hash, role) VALUES
('Admin User', 'admin@example.com', 'pbkdf2_sha256$200000$EFg76Cdij8lpBv5xe36luw==$eHAhik8Q4vfUP0lsJVSEg85LPn4d+5tqQXQ3vm7adT8=', 'admin'),
('Standard User', 'user@example.com', 'pbkdf2_sha256$200000$XGddoP7bYu0FxugAhbGELw==$3W/mi8iwAe8Oy6a8L1rOa+kQApLSWFdFWmY0LyTtQ80=', 'user')
ON CONFLICT (email) DO NOTHING;

INSERT INTO inventory.products (sku, name, description, active) VALUES
('HAMMER-001','Hammer','Steel claw hammer',TRUE),
('DRILL-001','Power Drill','Cordless drill',TRUE),
('SAW-001','Hand Saw','Wood cutting saw',TRUE),
('SCREWDRIVER-001','Screwdriver Set','Multi-head screwdriver set',TRUE),
('WRENCH-001','Adjustable Wrench','10-inch adjustable wrench',TRUE),
('PLIERS-001','Pliers','Slip-joint pliers',TRUE),
('TAPE-001','Measuring Tape','25-foot measuring tape',TRUE),
('LEVEL-001','Level','24-inch bubble level',TRUE),
('LADDER-001','Step Ladder','6-foot aluminum ladder',TRUE),
('GLOVES-001','Work Gloves','Heavy-duty grip gloves',TRUE)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO inventory.inventory_levels (product_id, quantity)
SELECT product_id, CASE sku
WHEN 'HAMMER-001' THEN 25 WHEN 'DRILL-001' THEN 8 WHEN 'SAW-001' THEN 14
WHEN 'SCREWDRIVER-001' THEN 30 WHEN 'WRENCH-001' THEN 12 WHEN 'PLIERS-001' THEN 18
WHEN 'TAPE-001' THEN 40 WHEN 'LEVEL-001' THEN 9 WHEN 'LADDER-001' THEN 5
WHEN 'GLOVES-001' THEN 50 ELSE 10 END
FROM inventory.products
ON CONFLICT (product_id) DO NOTHING;

INSERT INTO inventory.product_thresholds (product_id, threshold_qty, cooldown, enabled)
SELECT product_id, CASE sku
WHEN 'HAMMER-001' THEN 10 WHEN 'DRILL-001' THEN 5 WHEN 'SAW-001' THEN 6
WHEN 'SCREWDRIVER-001' THEN 10 WHEN 'WRENCH-001' THEN 5 WHEN 'PLIERS-001' THEN 6
WHEN 'TAPE-001' THEN 12 WHEN 'LEVEL-001' THEN 10 WHEN 'LADDER-001' THEN 6
WHEN 'GLOVES-001' THEN 15 ELSE 5 END, INTERVAL '12 hours', TRUE
FROM inventory.products
ON CONFLICT (product_id) DO NOTHING;
