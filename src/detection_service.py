from datetime import datetime, timezone
import time
from src.db import save_transaction
from src.ml_service import get_ml_score
from src.rule_engine import evaluate_rules
from src.shap_explainer import explain_transaction
from src.decision_engine import make_decision
from src.alert_service import evaluate_and_trigger_alert


FEATURE_COLUMNS = [
    "amount",
    "amount_vs_avg_ratio",
    "txn_count_last_5min",
    "time_since_last_txn_sec",
    "distance_from_last_location_km",
    "merchant_category_is_new_for_user"
]


def feature_reason_text(feature, value, shap_value):
    direction = "increased" if float(shap_value) > 0 else "decreased"

    return f"{feature}={value} {direction} fraud risk"


def generate_reason(rule_flags, ml_score, shap_result, decision):
    parts = []

    if rule_flags:
        parts.append("Triggered rules: " + ", ".join(rule_flags))
    else:
        parts.append("No deterministic rules triggered")

    parts.append(f"ML fraud score: {float(ml_score):.4f}")

    for item in shap_result["top_features"]:
        parts.append(
            feature_reason_text(
                item["feature"],
                item["feature_value"],
                item["shap_value"]
            )
        )

    parts.append(f"Decision: {decision.upper()}")

    return ". ".join(parts) + "."


def score_transaction(transaction):
    start_time = time.perf_counter()

    required_fields = [
        "transaction_id",
        "user_id",
        *FEATURE_COLUMNS
    ]

    missing_fields = [
        field for field in required_fields
        if field not in transaction
    ]

    if missing_fields:
        raise ValueError(f"Missing fields: {missing_fields}")

    features = {
        feature: transaction[feature]
        for feature in FEATURE_COLUMNS
    }

    ml_result = get_ml_score(features)
    rule_result = evaluate_rules(features)

    decision_result = make_decision(
        ml_result["ml_score"],
        rule_result
    )

    shap_result = explain_transaction(features, top_n=3)

    reason = generate_reason(
        decision_result["rule_flags"],
        ml_result["ml_score"],
        shap_result,
        decision_result["decision"]
    )
    decision_result["human_readable_reason"] = reason

    # ⭐ Option 2: Alerts system & Automated OTP triggering
    alert_info = evaluate_and_trigger_alert(
        transaction=transaction,
        decision_result=decision_result,
        ml_result=ml_result,
        rule_result=rule_result
    )

    latency_ms = (time.perf_counter() - start_time) * 1000

    result = {
        "transaction_id": transaction["transaction_id"],
        "user_id": transaction["user_id"],
        "amount": float(transaction["amount"]),
        "amount_vs_avg_ratio": float(transaction["amount_vs_avg_ratio"]),
        "txn_count_last_5min": int(transaction["txn_count_last_5min"]),
        "time_since_last_txn_sec": float(transaction["time_since_last_txn_sec"]),
        "distance_from_last_location_km": float(transaction["distance_from_last_location_km"]),
        "merchant_category_is_new_for_user": int(transaction["merchant_category_is_new_for_user"]),
        "risk_score": float(decision_result["risk_score"]),
        "rule_flags": list(decision_result["rule_flags"]),
        "ml_fraud_score": float(ml_result["ml_score"]),
        "decision": decision_result["decision"],
        "human_readable_reason": reason,
        "shap_top_features": shap_result.get("top_features", []),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "latency_ms": float(latency_ms),
        "alert_triggered": bool(alert_info is not None),
        "alert_id": alert_info["alert_id"] if alert_info else None,
        "alert_severity": alert_info["severity"] if alert_info else None,
        "otp_triggered": bool(alert_info and alert_info.get("otp_triggered")),
        "otp_status": "PENDING" if (alert_info and alert_info.get("otp_triggered")) else ("N/A" if decision_result["decision"] == "allow" else "NONE")
    }

    # ✅ Save to MongoDB
    save_transaction(result)

    return result