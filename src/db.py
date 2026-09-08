from pymongo import MongoClient, DESCENDING
from datetime import datetime, timezone
import logging

logger = logging.getLogger("streamsentinel.db")

MONGO_URI = "mongodb://127.0.0.1:27017/"
DB_NAME = "fraud_db"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500)
    db = client[DB_NAME]
    collection = db["transactions"]
    transactions_col = db["transactions"]
    alerts_col = db["alerts"]
    otps_col = db["otps"]
except Exception as e:
    logger.error(f"Failed to initialize MongoDB client: {e}")
    client = None
    db = None
    collection = None
    transactions_col = None
    alerts_col = None
    otps_col = None


def save_transaction(result):
    """Save a scored transaction to MongoDB."""
    if transactions_col is not None:
        try:
            return transactions_col.insert_one(result)
        except Exception as e:
            logger.error(f"Error saving transaction to MongoDB: {e}")
    return None


def get_recent_transactions(limit=100, filter_query=None):
    """Retrieve recent transactions sorted by processed_at descending."""
    if transactions_col is None:
        return []
    try:
        query = filter_query or {}
        cursor = transactions_col.find(query).sort("_id", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return []


def update_transaction_decision(transaction_id, new_decision, additional_fields=None):
    """Update decision/status for a transaction (e.g., after OTP verification)."""
    if transactions_col is None:
        return False
    try:
        update_data = {"$set": {"decision": new_decision}}
        if additional_fields:
            for k, v in additional_fields.items():
                update_data["$set"][k] = v
        update_data["$set"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = transactions_col.update_many({"transaction_id": transaction_id}, update_data)
        return res.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating transaction decision: {e}")
        return False


def save_alert(alert_data):
    """Save a fraud alert to MongoDB."""
    if alerts_col is not None:
        try:
            return alerts_col.insert_one(alert_data)
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
    return None


def get_recent_alerts(limit=50, severity=None):
    """Retrieve recent fraud alerts."""
    if alerts_col is None:
        return []
    try:
        query = {}
        if severity and severity != "ALL":
            query["severity"] = severity
        cursor = alerts_col.find(query).sort("_id", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return []


def acknowledge_alert(alert_id):
    """Mark an alert as acknowledged."""
    if alerts_col is None:
        return False
    try:
        res = alerts_col.update_one(
            {"alert_id": alert_id},
            {"$set": {"status": "ACKNOWLEDGED", "acknowledged_at": datetime.now(timezone.utc).isoformat()}}
        )
        return res.modified_count > 0
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return False


def save_otp_record(otp_record):
    """Save or update OTP record in MongoDB."""
    if otps_col is not None:
        try:
            return otps_col.insert_one(otp_record)
        except Exception as e:
            logger.error(f"Error saving OTP record: {e}")
    return None


def get_otp_records(user_id=None, limit=50):
    """Retrieve OTP records sorted by creation descending."""
    if otps_col is None:
        return []
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        cursor = otps_col.find(query).sort("_id", DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Error fetching OTP records: {e}")
        return []


def update_otp_record_status(user_id, status, otp_code=None):
    """Update status of the latest OTP record for a user."""
    if otps_col is None:
        return False
    try:
        query = {"user_id": user_id}
        if otp_code:
            query["otp"] = otp_code
        update = {
            "$set": {
                "status": status,
                "verified_at" if status == "VERIFIED" else "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        res = otps_col.update_many(query, update)
        return res.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating OTP record status: {e}")
        return False


def get_dashboard_metrics():
    """Aggregate high-level metrics for dashboard KPIs."""
    metrics = {
        "total_transactions": 0,
        "allow_count": 0,
        "review_count": 0,
        "otp_count": 0,
        "block_count": 0,
        "fraud_rate": 0.0,
        "avg_risk_score": 0.0,
        "total_alerts": 0,
        "critical_alerts": 0,
        "active_otps": 0,
    }
    if transactions_col is None:
        return metrics

    try:
        total = transactions_col.count_documents({})
        metrics["total_transactions"] = total
        if total > 0:
            pipeline = [
                {"$group": {
                    "_id": "$decision",
                    "count": {"$sum": 1},
                    "avg_risk": {"$avg": "$risk_score"}
                }}
            ]
            agg = list(transactions_col.aggregate(pipeline))
            total_risk = 0.0
            for item in agg:
                dec = (item["_id"] or "").lower()
                cnt = item["count"]
                if dec == "allow":
                    metrics["allow_count"] += cnt
                elif dec == "review":
                    metrics["review_count"] += cnt
                elif dec == "otp":
                    metrics["otp_count"] += cnt
                elif dec == "block":
                    metrics["block_count"] += cnt

            # All transactions risk average
            avg_cursor = list(transactions_col.aggregate([
                {"$group": {"_id": None, "overall_avg": {"$avg": "$risk_score"}}}
            ]))
            if avg_cursor and avg_cursor[0]["overall_avg"] is not None:
                metrics["avg_risk_score"] = float(avg_cursor[0]["overall_avg"])

            fraud_count = metrics["block_count"] + metrics["review_count"]
            metrics["fraud_rate"] = round((fraud_count / total) * 100, 2)

        if alerts_col is not None:
            metrics["total_alerts"] = alerts_col.count_documents({})
            metrics["critical_alerts"] = alerts_col.count_documents({"severity": "CRITICAL"})

        if otps_col is not None:
            now_iso = datetime.now(timezone.utc).isoformat()
            metrics["active_otps"] = otps_col.count_documents({"status": "PENDING"})

    except Exception as e:
        logger.error(f"Error calculating dashboard metrics: {e}")

    return metrics