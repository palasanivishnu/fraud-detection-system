import random
import uuid
from datetime import datetime, timedelta, timezone
from src.db import save_otp_record, get_otp_records, update_otp_record_status, update_transaction_decision

# In-memory storage for high-speed fallback & state tracking
otp_store = {}


def generate_otp(user_id, transaction_id=None):
    """
    Generate a 6-digit one-time password for a user.
    Optionally links the OTP to a specific transaction_id.
    Stores record in both memory and MongoDB.
    """
    otp = str(random.randint(100000, 999999))
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)
    otp_id = f"OTP_{uuid.uuid4().hex[:8].upper()}"

    record = {
        "otp_id": otp_id,
        "user_id": user_id,
        "transaction_id": transaction_id,
        "otp": otp,
        "status": "PENDING",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "attempts": 0
    }

    # Store in memory
    otp_store[user_id] = {
        "otp": otp,
        "transaction_id": transaction_id,
        "expires_at": expires_at,
        "status": "PENDING"
    }

    # Persist in MongoDB
    try:
        save_otp_record(record)
    except Exception as e:
        print(f"[OTP SERVICE WARNING] MongoDB save failed: {e}")

    print(f"[OTP SERVICE] Generated OTP for {user_id}: {otp} (Txn: {transaction_id or 'None'})")

    return otp


def verify_otp(user_id, entered_otp, transaction_id=None):
    """
    Verify entered OTP against memory and MongoDB.
    Updates status to VERIFIED or FAILED and marks linked transaction approved if valid.
    """
    # Try in-memory first
    if user_id in otp_store:
        data = otp_store[user_id]
        now = datetime.now(timezone.utc)

        # Check expiry
        if now > data["expires_at"]:
            update_otp_record_status(user_id, "EXPIRED", entered_otp)
            return False, "OTP expired"

        # Check match
        if str(data["otp"]).strip() != str(entered_otp).strip():
            return False, "Invalid OTP"

        # Success - update in-memory
        del otp_store[user_id]

        # Update MongoDB
        update_otp_record_status(user_id, "VERIFIED", entered_otp)

        # If transaction linked, update transaction state in MongoDB
        linked_txn = transaction_id or data.get("transaction_id")
        if linked_txn:
            update_transaction_decision(
                linked_txn,
                new_decision="allow",
                additional_fields={
                    "otp_verified": True,
                    "otp_verification_time": now.isoformat(),
                    "review_note": "Approved via successful OTP verification"
                }
            )

        return True, "OTP verified successfully"

    # Fallback: check MongoDB directly if not in memory
    records = get_otp_records(user_id=user_id, limit=5)
    now_iso = datetime.now(timezone.utc).isoformat()
    for rec in records:
        if rec.get("status") == "PENDING":
            if now_iso > rec.get("expires_at", ""):
                update_otp_record_status(user_id, "EXPIRED", rec.get("otp"))
                return False, "OTP expired"

            if str(rec.get("otp")).strip() == str(entered_otp).strip():
                update_otp_record_status(user_id, "VERIFIED", entered_otp)
                linked_txn = transaction_id or rec.get("transaction_id")
                if linked_txn:
                    update_transaction_decision(
                        linked_txn,
                        new_decision="allow",
                        additional_fields={
                            "otp_verified": True,
                            "otp_verification_time": now_iso,
                            "review_note": "Approved via successful OTP verification"
                        }
                    )
                return True, "OTP verified successfully"
            else:
                return False, "Invalid OTP"

    return False, "No OTP found"


def get_all_otps(limit=50):
    """Retrieve recent OTP records for UI dashboard display."""
    records = get_otp_records(limit=limit)
    if not records and otp_store:
        # Fallback to memory store if DB empty
        records = []
        for uid, val in otp_store.items():
            records.append({
                "user_id": uid,
                "transaction_id": val.get("transaction_id"),
                "otp": val.get("otp"),
                "status": val.get("status", "PENDING"),
                "expires_at": val.get("expires_at").isoformat() if hasattr(val.get("expires_at"), "isoformat") else str(val.get("expires_at")),
            })
    return records