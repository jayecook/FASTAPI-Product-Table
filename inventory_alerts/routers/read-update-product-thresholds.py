from fastapi import APIRouter, HTTPException
from inventory_alerts.db import connect_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ProductThresholdUpdateRequest(BaseModel):
    threshold_qty: Optional[int] = None
    cooldown: Optional[str] = None
    enabled: Optional[bool] = None

#Product thresholds/Read

@router.get("/product-thresholds")
def read_product_thresholds():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT product_id, threshold_qty, cooldown, enabled, updated_at
            FROM inventory.product_thresholds
            ORDER BY product_id
        """).fetchall()

    return [
        {
            "product_id": r[0],
            "threshold_qty": r[1],
            "cooldown": str(r[2]),
            "enabled": r[3],
            "updated_at": r[4],
        }
        for r in rows
    ]

@router.get("/product-thresholds/{product_id}")
def read_product_threshold(product_id: int):
    with connect_db() as conn:
        row = conn.execute("""
            SELECT product_id, threshold_qty, cooldown, enabled, updated_at
            FROM inventory.product_thresholds
            WHERE product_id = %s
        """, (product_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Product Threshold Not Found")

    return {
        "product_id": row[0],
        "threshold_qty": row[1],
        "cooldown": str(row[2]),
        "enabled": row[3],
        "updated_at": row[4],
    }

#Update

@router.patch("/product-thresholds/{product_id}")
def update_product_threshold(product_id: int, data: ProductThresholdUpdateRequest):
    update_data = data.dict(exclude_unset=True)

    if "threshold_qty" in update_data and update_data["threshold_qty"] is not None:
        if update_data["threshold_qty"] < 0:
            raise HTTPException(status_code=400, detail="Negative Threshold Quantity")

    updates = []
    values = []

    if "threshold_qty" in update_data:
        updates.append("threshold_qty = %s")
        values.append(update_data["threshold_qty"])

    if "cooldown" in update_data:
        updates.append("cooldown = %s::interval")
        values.append(update_data["cooldown"])

    if "enabled" in update_data:
        updates.append("enabled = %s")
        values.append(update_data["enabled"])

    if not updates:
        raise HTTPException(status_code=400, detail="No Valid Fields To Update")

    values.append(product_id)

    with connect_db() as conn:
        result = conn.execute(f"""
            UPDATE inventory.product_thresholds
            SET {", ".join(updates)}, updated_at = now()
            WHERE product_id = %s
            RETURNING product_id, threshold_qty, cooldown, enabled, updated_at
        """, tuple(values)).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Product Threshold Not Found")

    return {
        "product_id": result[0],
        "threshold_qty": result[1],
        "cooldown": str(result[2]),
        "enabled": result[3],
        "updated_at": result[4],
    }
