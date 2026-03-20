INSERT INTO inventory.alert_recipients (email)
VALUES
  ('employee1@company.com'),
  ('employee2@company.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO inventory.products (sku, name, description)
VALUES ('SKU-1002', 'USB-C Cable 1m', 'Braided USB-C cable')
ON CONFLICT (sku) DO NOTHING;

INSERT INTO inventory.product_thresholds (product_id, threshold_qty, cooldown, enabled)
SELECT product_id, 10, INTERVAL '12 hours', TRUE
FROM inventory.products
WHERE sku = 'SKU-1002'
ON CONFLICT (product_id) DO UPDATE
SET threshold_qty = EXCLUDED.threshold_qty,
    cooldown = EXCLUDED.cooldown,
    enabled = EXCLUDED.enabled;

INSERT INTO inventory.inventory_levels (product_id, quantity)
SELECT product_id, 50
FROM inventory.products
WHERE sku = 'SKU-1002'
ON CONFLICT (product_id) DO UPDATE
SET quantity = EXCLUDED.quantity;

UPDATE inventory.inventory_levels
SET quantity = 9
WHERE product_id = (SELECT product_id FROM inventory.products WHERE sku = 'SKU-1002');
