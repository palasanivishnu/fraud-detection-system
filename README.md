# 🛡️ StreamSentinel — Real-Time Financial Fraud Detection & Security Platform

StreamSentinel is an end-to-end, production-ready real-time financial fraud and anomaly detection platform. It combines behavioral machine learning (XGBoost), deterministic rule-based fraud detection, explainable AI (SHAP), MongoDB storage, an automated fraud alerting & OTP verification workflow, and an interactive Streamlit monitoring dashboard.

---

## 🚀 Features

- **Machine Learning Fraud Detection**: XGBoost Classifier trained on behavioral financial features.
- **Deterministic Rule Engine**: Evaluates high amounts, high velocity, impossible travel distance/time, and new merchant categories.
- **Hybrid Decision System**: Integrates ML probability and rule violation scores into calibrated decisions: `ALLOW`, `OTP`, `REVIEW`, and `BLOCK`.
- **Explainable AI (SHAP)**: Provides top feature impact explanations for every transaction in real-time.
- **⭐ Option 1 — Interactive Streamlit Dashboard**:
  - Live transactions feed with color-coded risk tags.
  - Deep-dive transaction inspector with SHAP feature impact cards.
  - Fraud alerts center with severity breakdown.
  - OTP verification portal for 2FA challenge approvals.
  - 1-Click demo simulator with preset attack scenarios.
- **⭐ Option 2 — Real-Time Alerts & Automated OTP**:
  - High-risk / fraudulent transactions automatically trigger security alerts (`CRITICAL`, `HIGH`, `WARNING`).
  - Suspicious transactions (`REVIEW` / `OTP`) **automatically trigger 6-digit OTP challenges**.
  - Successful OTP verification updates transaction state to approved in MongoDB.
- **MongoDB Storage**: Persists transactions, security alerts, and OTP lifecycle states.

---

## 📁 Repository Structure

```text
├── dashboard.py                  # Streamlit Interactive Monitoring Dashboard
├── run_dashboard.bat             # 1-click Windows launcher for dashboard
├── requirements.txt              # Project dependencies
├── test_alerts_and_otp.py        # Automated test suite for alerts & OTP workflow
├── test_detection.py             # Pipeline test script
├── test_otp.py                   # OTP verification test script
├── PERSON_B_HANDOFF.md           # Engineering subsystem handoff document
├── src/
│   ├── alert_service.py          # Option 2: Fraud alerts & automated OTP dispatcher
│   ├── otp_service.py            # OTP generation, storage, and verification
│   ├── detection_service.py      # Core transaction scoring orchestrator
│   ├── decision_engine.py        # Risk score calculation & classification
│   ├── rule_engine.py            # Deterministic rule evaluation
│   ├── ml_service.py             # ML inference wrapper
│   ├── ml_inference.py           # XGBoost prediction pipeline
│   ├── shap_explainer.py         # SHAP TreeExplainer integration
│   ├── feature_contract.py       # Input feature schema
│   ├── mongo_service.py          # Legacy MongoDB helper
│   └── db.py                     # MongoDB database layer (transactions, alerts, otps)
├── models/                       # Pre-trained models and engine configs
│   ├── xgboost_fraud_detector.json
│   ├── decision_engine_config.json
│   ├── rule_engine_config.json
│   ├── deployment_config.json
│   └── feature_columns.json
├── data/                         # Data directory (large CSVs gitignored)
├── notebooks/                    # Data exploration & model training notebooks
└── outputs/                      # Evaluation metrics & visualizations
```

---

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard
```bash
streamlit run dashboard.py
```
*Or double-click `run_dashboard.bat` on Windows.*
Open your browser at `http://localhost:8501`.

### 3. Run Automated Tests
```bash
python test_alerts_and_otp.py
```
