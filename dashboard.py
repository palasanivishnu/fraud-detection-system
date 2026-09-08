import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import uuid
import time

# Import project subsystems
from src.detection_service import score_transaction
from src.otp_service import generate_otp, verify_otp, get_all_otps
from src.alert_service import get_alerts_feed
from src.db import (
    get_recent_transactions,
    get_dashboard_metrics,
    acknowledge_alert,
    client as mongo_client
)

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="StreamSentinel — Fraud Detection Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium look & feel
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .decision-badge-allow {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .decision-badge-review {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .decision-badge-otp {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .decision-badge-block {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .alert-card-critical {
        border-left: 5px solid #EF4444;
        background-color: #FEF2F2;
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .alert-card-high {
        border-left: 5px solid #F59E0B;
        background-color: #FFFBEB;
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .alert-card-warning {
        border-left: 5px solid #3B82F6;
        background-color: #EFF6FF;
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("StreamSentinel")
    st.caption("AI-Powered Financial Fraud Detection")
    st.divider()

    # System Status
    st.subheader("System Health")
    mongo_status = "Connected (localhost:27017)" if mongo_client else "Disconnected"
    st.success(f"MongoDB: {mongo_status}")
    st.info("ML Model: XGBoost v2.0 (Loaded)")
    st.info("Rule Engine: 4 Active Rules")
    st.info("Explainer: SHAP TreeExplainer")

    st.divider()
    st.subheader("Auto-Refresh")
    auto_refresh = st.checkbox("Auto Refresh (every 8s)", value=False)
    if auto_refresh:
        time.sleep(8)
        st.rerun()

    if st.button("🔄 Refresh Data Now", use_container_width=True):
        st.rerun()

    st.divider()
    st.caption("StreamSentinel Project Demo • Option 1 & 2")

# -----------------------------------------------------------------------------
# HEADER & KPIS
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🛡️ StreamSentinel Fraud Monitoring & Alerts Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-Time Machine Learning, Deterministic Rules, Automated Alerts & OTP Verification</div>', unsafe_allow_html=True)

metrics = get_dashboard_metrics()

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
with kpi1:
    st.metric("Total Transactions", metrics["total_transactions"])
with kpi2:
    st.metric("Allowed (Normal)", metrics["allow_count"], delta="Approved", delta_color="normal")
with kpi3:
    st.metric("In Review / OTP", metrics["review_count"] + metrics["otp_count"], delta="Action Required", delta_color="off")
with kpi4:
    st.metric("Blocked (Fraud)", metrics["block_count"], delta=f"{metrics['fraud_rate']}% rate", delta_color="inverse")
with kpi5:
    st.metric("Active Alerts", metrics["total_alerts"], delta=f"{metrics['critical_alerts']} critical", delta_color="inverse")
with kpi6:
    st.metric("Pending OTPs", metrics["active_otps"], delta="2FA challenges", delta_color="off")

st.markdown("---")

# -----------------------------------------------------------------------------
# MAIN TABS INTERFACE
# -----------------------------------------------------------------------------
tab_txns, tab_alerts, tab_otp, tab_sim, tab_analytics = st.tabs([
    "💳 Transactions Feed",
    "🚨 Fraud Alerts (Option 2)",
    "🔐 OTP Verification Portal",
    "🧪 Live Demo Simulator",
    "📈 Analytics & Risk Metrics"
])

# -----------------------------------------------------------------------------
# TAB 1: TRANSACTIONS FEED
# -----------------------------------------------------------------------------
with tab_txns:
    st.subheader("Real-Time Transactions Stream")

    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 3])
    with col_filter1:
        decision_filter = st.selectbox(
            "Filter by Decision",
            ["ALL", "allow", "review", "block", "otp"],
            index=0
        )
    with col_filter2:
        risk_slider = st.slider("Minimum Risk Score", 0.0, 1.0, 0.0, 0.05)
    with col_filter3:
        user_search = st.text_input("Search by User ID or Txn ID", "").strip()

    # Query MongoDB
    query = {}
    if decision_filter != "ALL":
        query["decision"] = decision_filter
    if risk_slider > 0.0:
        query["risk_score"] = {"$gte": risk_slider}
    if user_search:
        query["$or"] = [
            {"user_id": {"$regex": user_search, "$options": "i"}},
            {"transaction_id": {"$regex": user_search, "$options": "i"}}
        ]

    txns = get_recent_transactions(limit=100, filter_query=query)

    if not txns:
        st.info("No transactions found matching the selected filters. Use the 'Live Demo Simulator' tab to score new transactions.")
    else:
        # Prepare display dataframe
        table_rows = []
        for t in txns:
            table_rows.append({
                "Txn ID": t.get("transaction_id", "N/A"),
                "User": t.get("user_id", "N/A"),
                "Amount ($)": f"${t.get('amount', 0.0):,.2f}",
                "Risk Score": f"{float(t.get('risk_score', 0.0)):.4f}",
                "ML Score": f"{float(t.get('ml_fraud_score', 0.0)):.4f}",
                "Decision": (t.get("decision") or "allow").upper(),
                "OTP Status": t.get("otp_status", "N/A"),
                "Alert": t.get("alert_severity", "None"),
                "Triggered Rules": ", ".join(t.get("rule_flags", [])) or "None",
                "Processed At": t.get("processed_at", "")[:19].replace("T", " ")
            })

        df_display = pd.DataFrame(table_rows)

        # Style decision column with colors
        def style_decision(val):
            if val == "ALLOW":
                return "background-color: #DEF7EC; color: #03543F; font-weight: bold;"
            elif val == "REVIEW":
                return "background-color: #FEF3C7; color: #92400E; font-weight: bold;"
            elif val == "BLOCK":
                return "background-color: #FDE8E8; color: #9B1C1C; font-weight: bold;"
            elif val == "OTP":
                return "background-color: #DBEAFE; color: #1E40AF; font-weight: bold;"
            return ""

        styled_df = df_display.style.map(style_decision, subset=["Decision"])
        st.dataframe(styled_df, use_container_width=True, height=350)

        # Detailed Transaction Drawer
        st.divider()
        st.subheader("🔍 Deep Dive Transaction Inspector")
        txn_ids = [t.get("transaction_id") for t in txns]
        selected_txn_id = st.selectbox("Select Transaction to Inspect", txn_ids, index=0)

        selected_txn = next((t for t in txns if t.get("transaction_id") == selected_txn_id), None)
        if selected_txn:
            d_col1, d_col2, d_col3 = st.columns([1, 1, 2])

            with d_col1:
                st.markdown(f"**Transaction ID:** `{selected_txn.get('transaction_id')}`")
                st.markdown(f"**User ID:** `{selected_txn.get('user_id')}`")
                st.markdown(f"**Amount:** `${selected_txn.get('amount', 0.0):,.2f}`")
                st.markdown(f"**Amount vs Avg Ratio:** `{selected_txn.get('amount_vs_avg_ratio', 1.0)}x`")
                st.markdown(f"**Txn Count (last 5 min):** `{selected_txn.get('txn_count_last_5min', 1)}`")

            with d_col2:
                st.markdown(f"**Distance from Last:** `{selected_txn.get('distance_from_last_location_km', 0.0)} km`")
                st.markdown(f"**Time Since Last:** `{selected_txn.get('time_since_last_txn_sec', 0.0)} sec`")
                st.markdown(f"**New Merchant Category:** `{'Yes' if selected_txn.get('merchant_category_is_new_for_user') else 'No'}`")
                st.markdown(f"**Latency:** `{selected_txn.get('latency_ms', 0.0):.2f} ms`")
                st.markdown(f"**OTP Status:** `{selected_txn.get('otp_status', 'N/A')}`")

            with d_col3:
                risk = float(selected_txn.get("risk_score", 0.0))
                dec = (selected_txn.get("decision") or "allow").upper()
                st.markdown(f"### Final Decision: **{dec}**")
                st.progress(min(max(risk, 0.0), 1.0), text=f"Combined Risk Score: {risk:.4f}")
                st.info(f"**Explainability Summary:**\n\n{selected_txn.get('human_readable_reason', 'N/A')}")

            # SHAP Top Feature Breakdown
            shap_features = selected_txn.get("shap_top_features", [])
            if shap_features:
                st.markdown("#### 🔬 SHAP Feature Impact Breakdown")
                shap_cols = st.columns(len(shap_features))
                for idx, feat in enumerate(shap_features):
                    with shap_cols[idx]:
                        val = feat.get("shap_value", 0.0)
                        dir_str = "Increased Risk" if val > 0 else "Decreased Risk"
                        st.metric(
                            label=feat.get("feature", "Feature"),
                            value=f"Val: {feat.get('feature_value')}",
                            delta=f"{val:+.3f} ({dir_str})",
                            delta_color="inverse" if val > 0 else "normal"
                        )

# -----------------------------------------------------------------------------
# TAB 2: FRAUD ALERTS FEED (OPTION 2)
# -----------------------------------------------------------------------------
with tab_alerts:
    st.subheader("🚨 Fraud Alerts Center (Option 2)")
    st.write("Real-time security alerts automatically dispatched when transactions exceed fraud thresholds or require multi-factor verification.")

    sev_filter = st.radio(
        "Alert Severity Filter",
        ["ALL", "CRITICAL", "HIGH", "WARNING"],
        horizontal=True
    )

    alerts = get_alerts_feed(limit=50, severity=sev_filter)

    if not alerts:
        st.success("🎉 No active fraud alerts matching this severity! The system is safe.")
    else:
        st.markdown(f"Showing **{len(alerts)}** recent security alerts:")
        for al in alerts:
            sev = al.get("severity", "WARNING")
            aid = al.get("alert_id")
            card_class = "alert-card-critical" if sev == "CRITICAL" else ("alert-card-high" if sev == "HIGH" else "alert-card-warning")
            status = al.get("status", "ACTIVE")

            with st.container():
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.1rem; font-weight: 700;">
                            {'🚨 [CRITICAL ALERT]' if sev == 'CRITICAL' else ('⚠️ [HIGH RISK ALERT]' if sev == 'HIGH' else '⚡ [SECURITY WARNING]')} {al.get('alert_id')}
                        </span>
                        <span style="font-size: 0.85rem; color: #64748B;">{al.get('timestamp', '')[:19].replace('T', ' ')} UTC</span>
                    </div>
                    <p style="margin-top: 8px; margin-bottom: 4px;">
                        <strong>Transaction:</strong> <code>{al.get('transaction_id')}</code> &nbsp;|&nbsp;
                        <strong>User:</strong> <code>{al.get('user_id')}</code> &nbsp;|&nbsp;
                        <strong>Risk Score:</strong> <code>{al.get('risk_score', 0.0):.4f}</code> &nbsp;|&nbsp;
                        <strong>Decision:</strong> <strong>{(al.get('decision') or '').upper()}</strong>
                    </p>
                    <p style="margin-bottom: 4px;">
                        <strong>Rules Triggered:</strong> {', '.join(al.get('rule_flags', [])) or 'None'}
                    </p>
                    <p style="margin-bottom: 4px; color: #1E3A8A;">
                        <strong>Action Executed:</strong> {al.get('action_taken', 'Alert Logged')}
                    </p>
                    {f'<p style="color: #065F46; font-weight: 600;">🔐 Triggered OTP Code: <code>{al.get("otp_code")}</code></p>' if al.get("otp_code") else ''}
                    <p style="font-size: 0.85rem; color: #475569; margin-top: 6px;">
                        <em>{al.get('human_readable_reason', '')}</em>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                c_ack, c_space = st.columns([1, 4])
                with c_ack:
                    if status == "ACTIVE":
                        if st.button(f"Acknowledge {aid}", key=f"ack_{aid}"):
                            acknowledge_alert(aid)
                            st.success("Alert Acknowledged!")
                            st.rerun()
                    else:
                        st.caption("✅ Acknowledged")

# -----------------------------------------------------------------------------
# TAB 3: OTP VERIFICATION PORTAL
# -----------------------------------------------------------------------------
with tab_otp:
    st.subheader("🔐 Multi-Factor OTP Verification Management")
    st.write("When a transaction is classified as `REVIEW` or elevated risk, StreamSentinel **automatically triggers an OTP challenge**. Users or reviewers can verify OTPs here to approve transactions.")

    otp_col1, otp_col2 = st.columns([1, 1])

    with otp_col1:
        st.markdown("### 🔑 Verify an OTP Challenge")
        with st.form("otp_verification_form"):
            user_input = st.text_input("User ID", placeholder="e.g. USER_BOB").strip()
            otp_code_input = st.text_input("Enter 6-Digit OTP Code", max_chars=6, placeholder="e.g. 723343").strip()
            linked_txn_input = st.text_input("Linked Transaction ID (Optional)", placeholder="e.g. TXN_SUSP_...").strip()

            submit_otp = st.form_submit_button("Verify OTP", use_container_width=True)

            if submit_otp:
                if not user_input or not otp_code_input:
                    st.error("Please provide both User ID and OTP code.")
                else:
                    success, message = verify_otp(
                        user_id=user_input,
                        entered_otp=otp_code_input,
                        transaction_id=linked_txn_input or None
                    )
                    if success:
                        st.success(f"✅ Success: {message}! Linked transaction has been approved.")
                    else:
                        st.error(f"❌ Verification Failed: {message}")

    with otp_col2:
        st.markdown("### 📋 Active & Recent OTP Records")
        all_otps = get_all_otps(limit=25)
        if not all_otps:
            st.info("No active OTP records in the system.")
        else:
            otp_table_data = []
            for item in all_otps:
                otp_table_data.append({
                    "User ID": item.get("user_id", "N/A"),
                    "Linked Txn": item.get("transaction_id", "N/A"),
                    "OTP Code": item.get("otp", "******"),
                    "Status": item.get("status", "PENDING"),
                    "Expires At": item.get("expires_at", "")[:19].replace("T", " ")
                })
            st.dataframe(pd.DataFrame(otp_table_data), use_container_width=True, height=300)

# -----------------------------------------------------------------------------
# TAB 4: LIVE TRANSACTION SIMULATOR (BEST FOR DEMO!)
# -----------------------------------------------------------------------------
with tab_sim:
    st.subheader("🧪 Live Transaction Simulator & Playground")
    st.write("Demonstrate the complete StreamSentinel engine live: adjust transaction features, execute ML + Rule scoring, observe explainability, and watch automatic alerts & OTPs trigger.")

    # Preset buttons
    st.markdown("#### ⚡ 1-Click Demo Scenarios")
    preset_cols = st.columns(4)

    preset_choice = None
    with preset_cols[0]:
        if st.button("🛒 Normal Grocery Purchase\n(Expected: ALLOW)", use_container_width=True):
            preset_choice = "legit"
    with preset_cols[1]:
        if st.button("⚠️ Sudden 8x Amount Spike\n(Expected: REVIEW -> OTP)", use_container_width=True):
            preset_choice = "spike"
    with preset_cols[2]:
        if st.button("🚨 Impossible Travel Attack\n(Expected: BLOCK -> Critical Alert)", use_container_width=True):
            preset_choice = "travel"
    with preset_cols[3]:
        if st.button("⚡ Rapid Carding Bot Attack\n(Expected: BLOCK -> High Velocity)", use_container_width=True):
            preset_choice = "velocity"

    # Default values based on presets
    if preset_choice == "legit":
        st.session_state["sim_amt"] = 35.50
        st.session_state["sim_ratio"] = 0.95
        st.session_state["sim_velocity"] = 1
        st.session_state["sim_time"] = 4200
        st.session_state["sim_dist"] = 1.2
        st.session_state["sim_new_merchant"] = 0
    elif preset_choice == "spike":
        st.session_state["sim_amt"] = 3200.0
        st.session_state["sim_ratio"] = 7.5
        st.session_state["sim_velocity"] = 2
        st.session_state["sim_time"] = 60
        st.session_state["sim_dist"] = 45.0
        st.session_state["sim_new_merchant"] = 1
    elif preset_choice == "travel":
        st.session_state["sim_amt"] = 1950.0
        st.session_state["sim_ratio"] = 6.0
        st.session_state["sim_velocity"] = 4
        st.session_state["sim_time"] = 15
        st.session_state["sim_dist"] = 1450.0
        st.session_state["sim_new_merchant"] = 1
    elif preset_choice == "velocity":
        st.session_state["sim_amt"] = 850.0
        st.session_state["sim_ratio"] = 3.5
        st.session_state["sim_velocity"] = 14
        st.session_state["sim_time"] = 8
        st.session_state["sim_dist"] = 80.0
        st.session_state["sim_new_merchant"] = 0

    st.markdown("---")
    st.markdown("#### 🎛️ Transaction Input Features")

    with st.form("simulator_form"):
        sim_c1, sim_c2 = st.columns(2)
        with sim_c1:
            in_txn_id = st.text_input("Transaction ID", value=f"TXN_DEMO_{uuid.uuid4().hex[:4].upper()}")
            in_user_id = st.text_input("User ID", value="USER_DEMO_01")
            in_amount = st.number_input("Amount ($)", min_value=1.0, max_value=100000.0, value=st.session_state.get("sim_amt", 50.0), step=10.0)
            in_ratio = st.number_input("Amount vs User Average Ratio", min_value=0.1, max_value=50.0, value=st.session_state.get("sim_ratio", 1.0), step=0.5)

        with sim_c2:
            in_velocity = st.number_input("Transaction Count in Last 5 Min", min_value=0, max_value=50, value=int(st.session_state.get("sim_velocity", 1)), step=1)
            in_time = st.number_input("Time Since Last Txn (seconds)", min_value=1, max_value=86400, value=int(st.session_state.get("sim_time", 1200)), step=10)
            in_dist = st.number_input("Distance from Last Location (km)", min_value=0.0, max_value=20000.0, value=float(st.session_state.get("sim_dist", 5.0)), step=10.0)
            in_new_mcc = st.selectbox("Merchant Category New for User?", [0, 1], index=int(st.session_state.get("sim_new_merchant", 0)), format_func=lambda x: "Yes (1)" if x == 1 else "No (0)")

        sim_submit = st.form_submit_button("🚀 Run Live Fraud Detection", use_container_width=True)

    if sim_submit:
        txn_payload = {
            "transaction_id": in_txn_id,
            "user_id": in_user_id,
            "amount": in_amount,
            "amount_vs_avg_ratio": in_ratio,
            "txn_count_last_5min": in_velocity,
            "time_since_last_txn_sec": in_time,
            "distance_from_last_location_km": in_dist,
            "merchant_category_is_new_for_user": in_new_mcc
        }

        with st.spinner("Analyzing transaction through XGBoost ML + Rule Engine..."):
            sim_result = score_transaction(txn_payload)

        # Show Results
        st.markdown("### 📊 Detection Results")
        res_col1, res_col2 = st.columns([1, 1])

        with res_col1:
            dec_label = (sim_result["decision"] or "allow").upper()
            if dec_label == "ALLOW":
                st.success(f"### Decision: 🟢 {dec_label}")
            elif dec_label in ["REVIEW", "OTP"]:
                st.warning(f"### Decision: 🟡 {dec_label}")
            else:
                st.error(f"### Decision: 🔴 {dec_label}")

            st.metric("Combined Risk Score", f"{sim_result['risk_score']:.4f}")
            st.metric("ML Fraud Score (XGBoost)", f"{sim_result['ml_fraud_score']:.4f}")
            st.metric("Inference Latency", f"{sim_result['latency_ms']:.2f} ms")

        with res_col2:
            st.markdown("#### 🛡️ Triggered Rules")
            if sim_result["rule_flags"]:
                for rf in sim_result["rule_flags"]:
                    st.error(f"🚩 Rule Triggered: **{rf}**")
            else:
                st.success("No deterministic fraud rules violated.")

            # Automated Option 2 Alert & OTP feedback
            if sim_result.get("alert_triggered"):
                st.warning(f"🚨 **Option 2 Alert Dispatched:** Severity `{sim_result.get('alert_severity')}` (ID: `{sim_result.get('alert_id')}`)")
            if sim_result.get("otp_triggered"):
                st.info(f"🔐 **Automated OTP Generated!** A 6-digit challenge code was triggered for `{in_user_id}` and is awaiting verification in the OTP Portal.")

        st.markdown("#### 💡 Human-Readable Decision Explanation")
        st.info(sim_result["human_readable_reason"])

        # SHAP Features
        if sim_result.get("shap_top_features"):
            st.markdown("#### 🔬 SHAP Feature Impact Breakdown")
            sh_cols = st.columns(len(sim_result["shap_top_features"]))
            for i, sh in enumerate(sim_result["shap_top_features"]):
                with sh_cols[i]:
                    sval = sh["shap_value"]
                    st.metric(
                        label=sh["feature"],
                        value=f"{sh['feature_value']}",
                        delta=f"{sval:+.3f}",
                        delta_color="inverse" if sval > 0 else "normal"
                    )

# -----------------------------------------------------------------------------
# TAB 5: ANALYTICS & RISK METRICS
# -----------------------------------------------------------------------------
with tab_analytics:
    st.subheader("📈 System Analytics & Risk Distributions")
    all_data = get_recent_transactions(limit=200)

    if not all_data:
        st.info("No transaction data available yet.")
    else:
        df_all = pd.DataFrame(all_data)

        chart_c1, chart_c2 = st.columns(2)

        with chart_c1:
            st.markdown("#### Decisions Distribution")
            if "decision" in df_all.columns:
                dec_counts = df_all["decision"].str.upper().value_counts().reset_index()
                dec_counts.columns = ["Decision", "Count"]
                st.bar_chart(dec_counts.set_index("Decision"))

        with chart_c2:
            st.markdown("#### Risk Score Distribution")
            if "risk_score" in df_all.columns:
                hist_values = np.histogram(df_all["risk_score"].astype(float), bins=10, range=(0, 1))[0]
                hist_df = pd.DataFrame({
                    "Risk Range": [f"{i/10:.1f}-{(i+1)/10:.1f}" for i in range(10)],
                    "Transactions": hist_values
                })
                st.bar_chart(hist_df.set_index("Risk Range"))

        # Top Triggered Rules Frequency
        st.markdown("#### Top Triggered Fraud Rules")
        rule_list = []
        for r_flags in df_all.get("rule_flags", []):
            if isinstance(r_flags, list):
                rule_list.extend(r_flags)
        if rule_list:
            rule_counts = pd.Series(rule_list).value_counts().reset_index()
            rule_counts.columns = ["Rule Name", "Times Triggered"]
            st.bar_chart(rule_counts.set_index("Rule Name"))
        else:
            st.info("No rules have been triggered in recent transactions.")
