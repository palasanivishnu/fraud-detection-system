from src.detection_service import score_transaction

data = {
    "transaction_id": "TXN_001",
    "user_id": "USER_001",
    "amount": 1000,
    "amount_vs_avg_ratio": 5.0,
    "txn_count_last_5min": 10,
    "time_since_last_txn_sec": 5,
    "distance_from_last_location_km": 100,
    "merchant_category_is_new_for_user": 1
}

result = score_transaction(data)

print(result)