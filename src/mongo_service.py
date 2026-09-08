from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["streamsentinel"]

transactions = db["transactions"]
flagged_transactions = db["flagged_transactions"]


def store_transaction(data):
    data["stored_at"] = datetime.utcnow()

    # store all
    transactions.insert_one(data)

    # store flagged only
    if data["decision"] != "allow":
        flagged_transactions.insert_one(data)

    print("Stored in MongoDB")