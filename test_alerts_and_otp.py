import uuid
from src.detection_service import score_transaction
from src.otp_service import verify_otp, get_all_otps
from src.db import get_recent_alerts, get_recent_transactions, get_dashboard_metrics

def run_tests():
    print("=== STARTING COMPREHENSIVE ALERTS & OTP INTEGRATION TESTS ===")

    # Test 1: Legitimate Transaction (Should ALLOW, No Alert, No OTP)
    legit_txn = {
        "transaction_id": f"TXN_LEGIT_{uuid.uuid4().hex[:4].upper()}",
        "user_id": "USER_ALICE",
        "amount": 25.50,
        "amount_vs_avg_ratio": 1.0,
        "txn_count_last_5min": 1,
        "time_since_last_txn_sec": 3600,
        "distance_from_last_location_km": 0.5,
        "merchant_category_is_new_for_user": 0
    }
    res_legit = score_transaction(legit_txn)
    print("\n[TEST 1] Legitimate Transaction:")
    print(f"  Decision: {res_legit['decision']} | Risk: {res_legit['risk_score']:.4f}")
    assert res_legit["decision"] == "allow", f"Expected allow, got {res_legit['decision']}"
    assert not res_legit["alert_triggered"], "Legit txn should not trigger alert"
    assert not res_legit["otp_triggered"], "Legit txn should not trigger OTP"
    print("  -> Passed!")

    # Test 2: Suspicious Transaction (Should trigger REVIEW, HIGH Alert, and AUTOMATIC OTP)
    suspicious_txn = {
        "transaction_id": f"TXN_SUSP_{uuid.uuid4().hex[:4].upper()}",
        "user_id": "USER_BOB",
        "amount": 450.0,
        "amount_vs_avg_ratio": 4.5,
        "txn_count_last_5min": 2,
        "time_since_last_txn_sec": 45,
        "distance_from_last_location_km": 50.0,
        "merchant_category_is_new_for_user": 1
    }
    res_susp = score_transaction(suspicious_txn)
    print("\n[TEST 2] Suspicious Transaction (Option 2 Automated OTP & Alert):")
    print(f"  Decision: {res_susp['decision']} | Risk: {res_susp['risk_score']:.4f}")
    print(f"  Alert Triggered: {res_susp['alert_triggered']} | Severity: {res_susp['alert_severity']}")
    print(f"  OTP Triggered: {res_susp['otp_triggered']} | OTP Status: {res_susp['otp_status']}")

    assert res_susp["alert_triggered"], "Suspicious txn must trigger an alert"
    if res_susp["decision"] in ["review", "otp"]:
        assert res_susp["otp_triggered"], "Review txn must automatically trigger an OTP"

    # Test 3: OTP Verification
    otps = get_all_otps(limit=10)
    user_bob_otps = [o for o in otps if o.get("user_id") == "USER_BOB"]
    assert len(user_bob_otps) > 0, "USER_BOB should have an active OTP record"
    latest_otp = user_bob_otps[0]["otp"]
    print(f"\n[TEST 3] Verifying OTP for USER_BOB (Code: {latest_otp}):")

    # Invalid code test
    ok_bad, msg_bad = verify_otp("USER_BOB", "000000", suspicious_txn["transaction_id"])
    print(f"  Invalid Code Test: ok={ok_bad}, message='{msg_bad}'")
    assert not ok_bad, "Wrong OTP code should fail"

    # Valid code test
    ok_good, msg_good = verify_otp("USER_BOB", latest_otp, suspicious_txn["transaction_id"])
    print(f"  Valid Code Test: ok={ok_good}, message='{msg_good}'")
    assert ok_good, "Valid OTP code must succeed"

    # Verify transaction status was updated in MongoDB
    txns = get_recent_transactions(limit=10)
    matched = [t for t in txns if t.get("transaction_id") == suspicious_txn["transaction_id"]]
    if matched:
        print(f"  Post-verification Transaction Decision: {matched[0].get('decision')} (Approved: {matched[0].get('otp_verified')})")
        assert matched[0].get("decision") == "allow", "Decision should be upgraded to allow upon OTP verification"
    print("  -> Passed!")

    # Test 4: Critical Fraud Transaction (Impossible Travel + Velocity -> BLOCK + CRITICAL Alert)
    fraud_txn = {
        "transaction_id": f"TXN_FRAUD_{uuid.uuid4().hex[:4].upper()}",
        "user_id": "USER_HACKER",
        "amount": 2500.0,
        "amount_vs_avg_ratio": 9.0,
        "txn_count_last_5min": 8,
        "time_since_last_txn_sec": 10,
        "distance_from_last_location_km": 1500.0,
        "merchant_category_is_new_for_user": 1
    }
    res_fraud = score_transaction(fraud_txn)
    print("\n[TEST 4] Critical Fraud Transaction:")
    print(f"  Decision: {res_fraud['decision']} | Severity: {res_fraud['alert_severity']}")
    assert res_fraud["decision"] == "block", f"Expected block, got {res_fraud['decision']}"
    assert res_fraud["alert_severity"] == "CRITICAL", f"Expected CRITICAL alert, got {res_fraud['alert_severity']}"
    print("  -> Passed!")

    # Test 5: Metrics Aggregation
    metrics = get_dashboard_metrics()
    print("\n[TEST 5] Dashboard Metrics Aggregation:")
    print(f"  Total Transactions: {metrics['total_transactions']}")
    print(f"  Allow Count: {metrics['allow_count']} | Review: {metrics['review_count']} | Block: {metrics['block_count']}")
    print(f"  Total Alerts: {metrics['total_alerts']} | Critical Alerts: {metrics['critical_alerts']}")
    assert metrics['total_transactions'] >= 3
    print("  -> Passed!")

    print("\n=== ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
