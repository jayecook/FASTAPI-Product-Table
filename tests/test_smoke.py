from inventory_alerts.db import connect_db, run_sql_file
from pathlib import Path


def test_schema_applies():
    with connect_db(autocommit=True) as conn:
        sql = Path(__file__).resolve().parents[1] / "inventory_alerts" / "sql" / "001_schema.sql"
        run_sql_file(conn, str(sql))

        # quick sanity: tables exist
        row = conn.execute("""
            SELECT to_regclass('inventory.products') IS NOT NULL AS ok
        """).fetchone()
        assert row[0] is True
