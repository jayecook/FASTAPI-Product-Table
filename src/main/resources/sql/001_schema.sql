CREATE SCHEMA IF NOT EXISTS inventory;

CREATE TABLE IF NOT EXISTS inventory.products (
  product_id BIGSERIAL PRIMARY KEY,
  sku TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_products_name_not_blank CHECK (btrim(name) <> ''),
  CONSTRAINT chk_products_sku_not_blank CHECK (btrim(sku) <> '')
);

CREATE TABLE IF NOT EXISTS inventory.inventory_levels (
  product_id BIGINT PRIMARY KEY REFERENCES inventory.products(product_id),
  quantity INTEGER NOT NULL CHECK (quantity >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory.product_thresholds (
  product_id BIGINT PRIMARY KEY REFERENCES inventory.products(product_id),
  threshold_qty INTEGER NOT NULL CHECK (threshold_qty >= 0),
  cooldown INTERVAL NOT NULL DEFAULT INTERVAL '12 hours',
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory.stock_alerts (
  alert_id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL REFERENCES inventory.products(product_id),
  quantity INTEGER NOT NULL,
  threshold_qty INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_stock_alerts_open
ON inventory.stock_alerts (product_id)
WHERE resolved_at IS NULL;

CREATE TABLE IF NOT EXISTS inventory.alert_recipients (
  recipient_id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE OR REPLACE FUNCTION inventory.set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_products_updated_at ON inventory.products;

CREATE TRIGGER trg_products_updated_at
BEFORE UPDATE ON inventory.products
FOR EACH ROW
EXECUTE FUNCTION inventory.set_updated_at();

CREATE OR REPLACE FUNCTION inventory.check_low_stock()
RETURNS trigger AS $$
DECLARE
  t_threshold INTEGER;
  t_enabled BOOLEAN;
  t_cooldown INTERVAL;
  last_alert TIMESTAMPTZ;
  has_open BOOLEAN;
BEGIN
  NEW.updated_at = now();

  SELECT threshold_qty, enabled, cooldown
  INTO t_threshold, t_enabled, t_cooldown
  FROM inventory.product_thresholds
  WHERE product_id = NEW.product_id;

  IF t_threshold IS NULL OR t_enabled IS DISTINCT FROM TRUE THEN
    RETURN NEW;
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM inventory.stock_alerts
    WHERE product_id = NEW.product_id AND resolved_at IS NULL
  ) INTO has_open;

  SELECT MAX(created_at)
  INTO last_alert
  FROM inventory.stock_alerts
  WHERE product_id = NEW.product_id;

  IF NEW.quantity < t_threshold THEN
    IF (NOT has_open) AND (last_alert IS NULL OR now() - last_alert >= t_cooldown) THEN
      INSERT INTO inventory.stock_alerts (product_id, quantity, threshold_qty)
      VALUES (NEW.product_id, NEW.quantity, t_threshold);

      PERFORM pg_notify(
        'low_stock',
        json_build_object(
          'product_id', NEW.product_id,
          'quantity', NEW.quantity,
          'threshold', t_threshold,
          'created_at', now()
        )::text
      );
    END IF;
  ELSE
    UPDATE inventory.stock_alerts
    SET resolved_at = now()
    WHERE product_id = NEW.product_id AND resolved_at IS NULL;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_inventory_low_stock_update ON inventory.inventory_levels;
DROP TRIGGER IF EXISTS trg_inventory_low_stock_insert ON inventory.inventory_levels;

CREATE TRIGGER trg_inventory_low_stock_update
BEFORE UPDATE OF quantity ON inventory.inventory_levels
FOR EACH ROW
EXECUTE FUNCTION inventory.check_low_stock();

CREATE TRIGGER trg_inventory_low_stock_insert
BEFORE INSERT ON inventory.inventory_levels
FOR EACH ROW
EXECUTE FUNCTION inventory.check_low_stock();

CREATE OR REPLACE VIEW inventory.v_open_stock_alerts AS
SELECT
  a.alert_id,
  a.created_at,
  p.sku,
  p.name,
  a.quantity,
  a.threshold_qty
FROM inventory.stock_alerts a
JOIN inventory.products p ON p.product_id = a.product_id
WHERE a.resolved_at IS NULL
ORDER BY a.created_at DESC;
