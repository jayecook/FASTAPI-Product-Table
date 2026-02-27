from fastapi import APIRouter, HTTPException
from inventory_alerts.db import connect_db

router = APIRouter()

#Open Alerts/Read Only

@router.get("/open-alerts")
def read_open_alerts():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT alert_id, created_at, sku, name, quantity, threshold_qty
            FROM inventory.v_open_stock_alerts
            ORDER BY created_at DESC
        """).fetchall()

    return [
        {
            "alert_id": r[0],
            "created_at": r[1],
            "sku": r[2],
            "name": r[3],
            "quantity": r[4],
            "threshold_qty": r[5],
        }
        for r in rows
    ]

@router.get("/open-alerts/{alert_id}")
def read_open_alert(alert_id: int):
    with connect_db() as conn:
        row = conn.execute("""
            SELECT alert_id, created_at, sku, name, quantity, threshold_qty
            FROM inventory.v_open_stock_alerts
            WHERE alert_id = %s
        """, (alert_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Open Alert Not Found")

    return {
        "alert_id": row[0],
        "created_at": row[1],
        "sku": row[2],
        "name": row[3],
        "quantity": row[4],
        "threshold_qty": row[5],
    }