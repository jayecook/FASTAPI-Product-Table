from fastapi import APIRouter, HTTPException
from inventory_alerts.db import connect_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AlertRecipientUpdateRequest(BaseModel):
    email: Optional[str] = None
    enabled: Optional[bool] = None

#Alert Recipients/Read

@router.get("/alert-recipients")
def read_alert_recipients():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT recipient_id, email, enabled
            FROM inventory.alert_recipients
            ORDER BY recipient_id
        """).fetchall()

    return [
        {
            "recipient_id": r[0],
            "email": r[1],
            "enabled": r[2],
        }
        for r in rows
    ]

@router.get("/alert-recipients/{recipient_id}")
def read_alert_recipient(recipient_id: int):
    with connect_db() as conn:
        row = conn.execute("""
            SELECT recipient_id, email, enabled
            FROM inventory.alert_recipients
            WHERE recipient_id = %s
        """, (recipient_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Alert Recipient Not Found")

    return {
        "recipient_id": row[0],
        "email": row[1],
        "enabled": row[2],
    }

#Update

@router.patch("/alert-recipients/{recipient_id}")
def update_alert_recipient(recipient_id: int, data: AlertRecipientUpdateRequest):
    update_data = data.dict(exclude_unset=True)

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = update_data["email"].strip()
        if not update_data["email"]:
            raise HTTPException(status_code=400, detail="Blank Email")

    updates = []
    values = []

    for key, value in update_data.items():
        updates.append(f"{key} = %s")
        values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No Valid Fields To Update")

    values.append(recipient_id)

    with connect_db() as conn:
        result = conn.execute(f"""
            UPDATE inventory.alert_recipients
            SET {", ".join(updates)}
            WHERE recipient_id = %s
            RETURNING recipient_id, email, enabled
        """, tuple(values)).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Alert Recipient Not Found")

    return {
        "recipient_id": result[0],
        "email": result[1],
        "enabled": result[2],
    }
