# StreamSentinel
# Person B → Person C Handoff
# Fraud Detection ML Subsystem — V2.1

---

## 1. Purpose

This document explains the current state of the StreamSentinel project from Person B's side and defines the handoff from the Person B detection subsystem to Person C.

It is intended to be read by:

- Person C
- Person C's coding assistant
- Any developer integrating the Person B detection subsystem

The purpose of this document is to explain:

- What the overall project does
- What Person B has completed
- What is already available in this project
- What Person C is responsible for
- The interface between Person B and Person C
- Where Person C should start
- Which existing components should be treated as completed Person B work

This document is a handoff and integration guide. It is not a replacement for the source code.

---

# 2. Project Overview

StreamSentinel is a real-time financial fraud and anomaly detection system.

The purpose of the system is to analyze financial transactions as they occur and determine the level of risk associated with each transaction.

The final system combines:

- Behavioral transaction features
- Rule-based fraud detection
- XGBoost machine learning
- Decision logic
- SHAP explainability

The system produces one of four final decisions:

- Allow
- OTP
- Review
- Block

The overall project flow is:

Transaction Simulator
        ↓
Kafka
        ↓
Redis / Stateful Processing
        ↓
Feature Vector
        ↓
Person B Detection Subsystem
        ↓
Scoring Output
        ↓
Person C Platform / Monitoring Layer

The Person B subsystem is the detection layer between the Feature Vector and the Scoring Output.

---

# 3. Overall Team Responsibilities

## Person A

Person A is responsible for the transaction and streaming side of the project.

Main responsibilities include:

- Transaction simulator
- Kafka producer
- Kafka partitioning
- Kafka consumer
- Redis-based state
- Stateful behavioral processing
- Production of the Feature Vector required by Person B

Person A provides the input required by Person B.

---

## Person B

Person B is responsible for the fraud detection and decision-making layer.

Main responsibilities include:

- Behavioral ML feature engineering
- XGBoost fraud detection
- Model evaluation
- Model tuning
- SHAP explainability
- Rule Engine
- Decision Engine
- Rule + ML integration
- Human-readable detection reasons
- Production detection service
- Scoring Output

The Person B detection subsystem is completed through Phase 11.

---

## Person C

Person C is responsible for the platform, storage, monitoring, alerting, API, deployment, and integration layer.

Main responsibilities include:

- MongoDB
- Prometheus
- Grafana
- Webhook alerting
- FastAPI
- OTP workflow
- Docker / Docker Compose integration
- Deployment
- AWS EC2 deployment
- Locust/load testing
- Final platform integration

Person C consumes the output produced by Person B.

---

# 4. Current Person B Status

Person B's core detection responsibility is complete through Phase 11.

The following work has been completed:

## Phase 1 — Data Exploration

Completed.

The fraud dataset was explored and validated for use in the project.

---

## Phase 2 — Data Preprocessing

Completed.

The raw transaction data was cleaned, validated, standardized, and prepared for feature engineering.

---

## Phase 3 — Behavioral Feature Engineering

Completed.

The six behavioral/ML features used by the current detection model are:

- `amount`
- `amount_vs_avg_ratio`
- `txn_count_last_5min`
- `time_since_last_txn_sec`
- `distance_from_last_location_km`
- `merchant_category_is_new_for_user`

The engineered features were created using past transaction information so that the feature generation is suitable for fraud detection without using future information.

---

## Phase 4 — XGBoost Model Development

Completed.

An XGBoost fraud detection model was developed using the project transaction features.

Class imbalance was handled during model development.

---

## Phase 5 — Hyperparameter Tuning

Completed.

The XGBoost model was tuned and compared with the baseline model.

---

## Phase 6 — Final Model Evaluation

Completed.

The model was evaluated using:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC
- Confusion Matrix
- ROC Curve
- Precision-Recall Curve

The deployment candidate was selected and validated.

---

## Phase 7 — SHAP Explainability

Completed.

SHAP explainability was added to provide feature-level reasoning for the ML result.

The detection subsystem can produce human-readable explanations for suspicious decisions.

---

## Phase 8 — Model Deployment Preparation

Completed.

The production model and deployment-related configuration files were created.

The official deployment model is:

`models/xgboost_fraud_detector.json`

---

## Phase 9 — Rule Engine

Completed.

The current Rule Engine contains exactly four rules:

- `HIGH_AMOUNT`
- `HIGH_VELOCITY`
- `IMPOSSIBLE_TRAVEL`
- `NEW_MERCHANT_CATEGORY`

There is no device-trust rule in the current implementation.

---

## Phase 10 — Decision Engine

Completed.

The Decision Engine combines the ML fraud score and rule score to produce the final risk score and decision.

Current decisions are:

- Allow
- OTP
- Review
- Block

The Decision Engine and its validation were completed successfully.

---

## Phase 11 — Rule + ML + SHAP Integration

Completed.

The complete Person B detection pipeline has been integrated:

Feature Vector
        ↓
Rule Engine
        ↓
XGBoost / ML Inference
        ↓
Decision Engine
        ↓
SHAP Explanation
        ↓
Human-Readable Reason
        ↓
Scoring Output

The production detection service and integration validation were completed successfully.

---

# 5. Current Person B Project Structure

The current project structure has already been created and should be treated as the existing V2.1 project structure.

The main areas are:

```text
Fraud-detection-ML-V2/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── models/
│
├── notebooks/
│
├── outputs/
│   ├── figures/
│   ├── metrics/
│   └── reports/
│
├── src/
│
├── README.md
└── requirements.txt


---

# 6. Person C Integration Starting Point

This section explains exactly where Person C should begin from the existing Person B project.

Person C does not need to rebuild the Person B fraud detection system.

The existing Person B implementation already produces the required **Scoring Output**.

The main integration entry point is:

```text
src/detection_service.py

Person C should first inspect this file to understand how the completed Person B detection pipeline is called and what it returns.

The Person C workflow starts from the output of this service.

7. Where Person C Gets the Scoring Output

The Scoring Output is produced by:

src/detection_service.py

The detection service receives the Feature Vector and runs the completed Person B pipeline:

Feature Vector
      ↓
Rule Engine
      ↓
XGBoost
      ↓
Decision Engine
      ↓
SHAP
      ↓
Human-Readable Reason
      ↓
Scoring Output

Therefore, Person C should treat:

src/detection_service.py

as the boundary between Person B and Person C.

Person C does not need to manually calculate:

risk_score
ml_fraud_score
rule_flags
decision
human_readable_reason

These values are already produced by Person B.

Person C's responsibility is to receive the completed Scoring Output and use it in the platform layer.

8. Person B → Person C Data Flow

The handoff is:

Person A
   ↓
Feature Vector
   ↓
src/detection_service.py
   ↓
Person B Detection
   ↓
Scoring Output
   ↓
Person C Platform

The complete Scoring Output contains:

transaction_id
user_id
risk_score
rule_flags
ml_fraud_score
decision
human_readable_reason
processed_at
latency_ms

Person C should use this output as the input to the downstream platform components.

9. Scoring Output Example

An example Scoring Output is:

{
  "transaction_id": "TXN001",
  "user_id": "USER001",
  "risk_score": 0.62,
  "rule_flags": [
    "HIGH_AMOUNT"
  ],
  "ml_fraud_score": 0.71,
  "decision": "OTP",
  "human_readable_reason": "High transaction amount compared with user's normal behavior.",
  "processed_at": "2026-09-05T20:00:00",
  "latency_ms": 8.4
}

This output is what Person C should consume.

10. How Person C Should Use the Scoring Output

Person C should think of the Scoring Output as the central result of the fraud detection pipeline.

The downstream flow is:

Scoring Output
      ↓
 ┌───────────────┬────────────────┬────────────────┬────────────────┐
 ↓               ↓                ↓                ↓
MongoDB       Prometheus        Alerts          Application/API
 ↓               ↓                ↓
Storage       Metrics          Webhooks
                ↓
              Grafana

The same Scoring Output can therefore be used by different Person C components for different purposes.

11. MongoDB Integration

Person C should use the Scoring Output to store the detection result in MongoDB.

The MongoDB record should preserve the important output information, including:

transaction_id
user_id
risk_score
rule_flags
ml_fraud_score
decision
human_readable_reason
processed_at
latency_ms

The purpose of MongoDB is to provide persistent storage for transaction detection results and audit information.

The Person C application should receive the Scoring Output and pass the result to the MongoDB persistence layer.

Conceptually:

Scoring Output
      ↓
Person C Application
      ↓
MongoDB

Person C should not create a second fraud score for the database.

The database should reflect the result returned by Person B.

12. Prometheus Integration

Person C should use the Scoring Output and the running application to expose appropriate operational metrics.

Useful information can include:

number of transactions processed
number of Allow decisions
number of OTP decisions
number of Review decisions
number of Block decisions
detection latency
processing errors
service health
rule-trigger activity

The latency_ms field supplied by Person B can be used as detection-side latency information.

Prometheus is responsible for collecting monitoring metrics, not for performing fraud detection.

Conceptually:

Detection Service
      ↓
Person C Metrics Layer
      ↓
Prometheus
13. Grafana Integration

Person C should use Prometheus metrics to create Grafana dashboards.

The dashboards should provide visibility into the running system.

Possible dashboard areas include:

Transaction Activity
Decision Distribution
Fraud / Detection Activity
Rule Activity
Latency
Errors
System Health

The dashboard is a visualization/monitoring layer.

Fraud scoring itself remains the responsibility of Person B.

14. Webhook Alert Integration

Person C should use the final decision from the Scoring Output to determine when platform-level alerts are required.

For example, relevant high-risk decisions can be connected to webhook notifications:

Scoring Output
      ↓
decision
      ↓
Alerting Logic
      ↓
Webhook

Possible high-risk decisions include:

Review
Block

The alerting layer should use the decision already produced by Person B rather than creating another fraud decision system.

The appropriate alert format and destination are part of Person C's implementation.

15. FastAPI Integration

Person C is responsible for the FastAPI/API layer.

The API layer should connect the platform components without changing the underlying Person B detection logic.

A possible high-level flow is:

API / Platform
      ↓
Detection Service
      ↓
Scoring Output
      ↓
Storage / Monitoring / Alerts

The exact API design belongs to Person C's implementation.

16. OTP Flow

When the Person B Scoring Output contains:

decision = OTP

Person C handles the OTP workflow.

The expected project behavior is:

Transaction
     ↓
Person B
     ↓
decision = OTP
     ↓
Person C OTP Flow
     ↓
OTP Verification

The project includes a mocked OTP process.

Person C is responsible for:

OTP generation/storage
OTP verification
successful verification handling
incorrect OTP handling
expiration handling
API endpoint for verification

The project uses a 60-second OTP timeout.

The OTP mechanism is a Person C responsibility, not a Person B responsibility.

17. Decision-Based Platform Behavior

Person C should use the final decision from Person B as the basis for downstream platform behavior.

The four possible outcomes are:

Allow
OTP
Review
Block

High-level behavior:

Allow
  ↓
Normal successful transaction flow

OTP
  ↓
OTP verification flow

Review
  ↓
Review / alert / persistence flow

Block
  ↓
Block / alert / persistence flow

The exact platform behavior should be implemented by Person C.

The fraud decision itself is already produced by Person B.

18. Person C Integration With Person A

The eventual full system will receive transactions from Person A.

Person A produces the Feature Vector.

Person B consumes the Feature Vector.

Person B produces the Scoring Output.

Person C consumes the Scoring Output.

The complete chain is:

PERSON A
Transaction Simulator
      ↓
Kafka
      ↓
Stateful Consumer
      ↓
Redis
      ↓
Feature Vector
      ↓
PERSON B
Detection Service
      ↓
Rule + ML + SHAP
      ↓
Scoring Output
      ↓
PERSON C
MongoDB
Prometheus
Grafana
Alerts
FastAPI
OTP
Deployment
19. Person C Can Begin Without Waiting for Person A

Person C can start development using sample/mock Feature Vectors.

The initial goal is to verify:

Feature Vector
      ↓
Person B Detection Service
      ↓
Scoring Output
      ↓
Person C Platform

Once Person A's Kafka/Redis pipeline is ready, the mock Feature Vector source can be replaced by Person A's real Feature Vector.

This allows Person C to begin his work independently.

20. Recommended Order for Person C

Person C should proceed from the existing Person B project in this order:

Step 1 — Understand the existing project

Read this handoff document.

Then inspect the current source and model structure.

Step 2 — Understand the Person B entry point

Open:

src/detection_service.py

Understand how the detection subsystem receives input and returns output.

Step 3 — Verify the B → C boundary

Use a sample Feature Vector and verify that a Scoring Output is produced.

The important thing to confirm is:

Input:
Feature Vector

Output:
Scoring Output
Step 4 — Integrate the output

Use the Scoring Output as the input to the Person C platform layer.

Step 5 — Build the platform components

Proceed with the Person C responsibilities around the Scoring Output:

MongoDB
Prometheus
Grafana
Webhook Alerts
FastAPI
OTP
Docker / Compose
Deployment
Locust
Step 6 — Connect the complete system

After the platform layer works locally, integrate the real Person A streaming pipeline.

21. What Person C Should Read in the Existing Project

The primary Person B integration file is:

src/detection_service.py

After that, the most relevant files for understanding the detection subsystem are:

src/feature_contract.py
src/ml_inference.py
src/ml_service.py
src/rule_engine.py
src/decision_engine.py
src/shap_explainer.py

The relevant deployment artifacts are in:

models/

Important model/configuration files include:

models/xgboost_fraud_detector.json
models/feature_columns.json
models/model_info.json
models/deployment_config.json
models/deployment_manifest.json
models/rule_engine_config.json
models/decision_engine_config.json

Person C does not need to modify these files just to begin platform integration.

They are primarily there to support the existing Person B detection subsystem.

22. Existing Outputs and Development Artifacts

The project also contains:

data/
notebooks/
outputs/

These contain the data, development notebooks, evaluation results, reports and figures produced during Person B development.

They provide development and documentation context.

For normal downstream integration, Person C should focus primarily on:

src/
models/

and especially:

src/detection_service.py

The notebooks are not the normal runtime interface.

23. Important Separation of Responsibilities

The following separation should be maintained:

PERSON A
Produces Feature Vector

PERSON B
Produces Scoring Output

PERSON C
Consumes Scoring Output
and builds the downstream platform

Person C should not depend on notebook execution for normal application runtime.

The production detection interface is the code under src/, with:

src/detection_service.py

as the main integration entry point.

24. What Is Already Done vs What Remains
Already completed by Person B
Data preparation
Behavioral feature engineering
XGBoost development
XGBoost tuning
Model evaluation
Model deployment preparation
SHAP explainability
Rule Engine
Decision Engine
Rule + ML + SHAP integration
Detection service
Scoring Output
Remaining for Person C
Consume Scoring Output
MongoDB
Prometheus
Grafana
Webhook alerts
FastAPI
OTP workflow
Docker / Docker Compose integration
Deployment
AWS EC2
Locust / load testing
Final platform integration
25. Important Instruction for the Coding Assistant

The existing Person B detection subsystem should be treated as completed project work.

The coding assistant should:

Understand the existing code before making changes
Use src/detection_service.py as the main Person B integration point
Preserve the existing Feature Vector and Scoring Output interface
Avoid rebuilding the XGBoost/rule/SHAP/decision system
Focus development on Person C's assigned responsibilities
Use mock/sample Feature Vectors for initial integration where necessary
Connect the resulting Scoring Output to the downstream platform components
Integrate Person A's real streaming input later

Any changes to the Person B detection logic should be made only when genuinely required for integration compatibility.

26. Final Starting Point for Person C

The Person C starting point is:

Existing Person B project
        ↓
src/detection_service.py
        ↓
Understand Feature Vector input
        ↓
Understand Scoring Output
        ↓
Verify local detection result
        ↓
Build Person C platform layer
        ↓
MongoDB
Prometheus
Grafana
Alerts
FastAPI
OTP
Deployment
Load Testing
        ↓
Integrate Person A
        ↓
Full End-to-End System

The key principle is:

Person B provides the fraud detection result. Person C builds the platform around that result.

27. Person B → Person C Contract Summary
INPUT TO PERSON B
-----------------
Feature Vector

transaction_id
user_id
amount
amount_vs_avg_ratio
txn_count_last_5min
time_since_last_txn_sec
distance_from_last_location_km
merchant_category_is_new_for_user


OUTPUT FROM PERSON B
--------------------
Scoring Output

transaction_id
user_id
risk_score
rule_flags
ml_fraud_score
decision
human_readable_reason
processed_at
latency_ms


PERSON C USES THE OUTPUT FOR
----------------------------
MongoDB
Prometheus
Grafana
Webhook Alerts
FastAPI
OTP
Deployment
Load Testing
Final Platform Integration
28. End State

The final system should operate as one integrated pipeline:

Transaction
     ↓
Kafka
     ↓
Redis / Stateful Processing
     ↓
Feature Vector
     ↓
Person B Detection
     ↓
Risk Score + Decision + Explanation
     ↓
Scoring Output
     ↓
Person C Platform
     ↓
MongoDB
Prometheus
Grafana
Alerts
OTP
API
Deployment

Person B's responsibility ends at producing the Scoring Output.

Person C's responsibility begins with consuming that Scoring Output and completing the downstream platform functionality.