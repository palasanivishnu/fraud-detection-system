import uuid
from datetime import datetime, timezone
import logging
from src.db import save_alert, get_recent_alerts, acknowledge_alert
from src.otp_service import generate_otp

logger = logging.getLogger("streamsentinel.alerts")


def get_alert_severity(decision, risk_score, rule_flags):
    """
    Determine alert severity based on decision, combined risk score, and triggered rules.
    Returns: 'CRITICAL', 'HIGH', 'WARNING', or None
    """
    decision_lower = str(decision).lower()

    if decision_lower == "block" or "IMPOSSIBLE_TRAVEL" in rule_flags or risk_score >= 0.75:
        return "CRITICAL"
    elif decision_lower == "review" or risk_score >= 0.50 or "HIGH_VELOCITY" in rule_flags:
        return "HIGH"
    elif decision_lower == "otp" or risk_score >= 0.25:
        return "WARNING"

    return None


def evaluate_and_trigger_alert(transaction, decision_result, ml_result=None, rule_result=None):
    """
    Option 2 — Alerts System:
    Evaluates transaction risk. When fraud or suspicious activity happens:
    1. Sends / logs a structured security alert
    2. Automatically triggers an OTP when verification is needed (REVIEW or OTP decision)
    3. Persists alert into MongoDB
    """
    decision = decision_result.get("decision", "allow")
    risk_score = float(decision_result.get("risk_score", 0.0))
    rule_flags = decision_result.get("rule_flags", [])
    transaction_id = transaction.get("transaction_id", f"TXN_{uuid.uuid4().hex[:6].upper()}")
    user_id = transaction.get("user_id", "UNKNOWN_USER")

    severity = get_alert_severity(decision, risk_score, rule_flags)

    # If legitimate transaction and below warning threshold, no alert is needed
    if not severity and decision.lower() == "allow":
        return None

    # Fallback to WARNING if allow but somehow flag was raised
    if not severity:
        severity = "WARNING"

    # Option 2 requirement: Trigger OTP automatically when verification is required
    otp_triggered = False
    otp_code = None
    action_taken = ""

    if decision.lower() in ["review", "otp"]:
        otp_code = generate_otp(user_id=user_id, transaction_id=transaction_id)
        otp_triggered = True
        action_taken = f"Automated OTP Triggered for user {user_id} (Challenge Verification)"
    elif decision.lower() == "block":
        action_taken = f"Transaction {transaction_id} BLOCKED immediately. Account flagged."
    else:
        action_taken = "Flagged for monitoring"

    alert_id = f"ALT_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    alert_data = {
        "alert_id": alert_id,
        "transaction_id": transaction_id,
        "user_id": user_id,
        "severity": severity,
        "decision": decision,
        "risk_score": risk_score,
        "rule_flags": rule_flags,
        "ml_fraud_score": float(ml_result.get("ml_score", 0.0)) if ml_result else None,
        "action_taken": action_taken,
        "otp_triggered": otp_triggered,
        "otp_code": otp_code,
        "timestamp": timestamp,
        "status": "ACTIVE",
        "human_readable_reason": decision_result.get("human_readable_reason", "")
    }

    # Console display for demo and logging
    banner_border = "=" * 80
    if severity == "CRITICAL":
        icon = "[CRITICAL FRAUD ALERT]"
    elif severity == "HIGH":
        icon = "[HIGH RISK ALERT]"
    else:
        icon = "[SECURITY NOTICE]"

    print(f"\n{banner_border}")
    print(f"{icon} ID: {alert_id}")
    print(f"  Transaction: {transaction_id} | User: {user_id} | Amount: ${transaction.get('amount', 0)}")
    print(f"  Decision: {decision.upper()} | Risk Score: {risk_score:.4f}")
    if rule_flags:
        print(f"  Triggered Rules: {', '.join(rule_flags)}")
    print(f"  Action Taken: {action_taken}")
    if otp_triggered:
        print(f"  [OTP] Auto-Generated OTP: {otp_code}")
    print(f"{banner_border}\n")

    # Save to MongoDB
    try:
        save_alert(alert_data)
    except Exception as e:
        logger.error(f"Failed to persist alert in MongoDB: {e}")

    return alert_data


def get_alerts_feed(limit=50, severity=None):
    """Retrieve active and recent alerts from MongoDB for UI and reporting."""
    return get_recent_alerts(limit=limit, severity=severity)
