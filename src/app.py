# =====================================================================
# PROJECT: Smart Pharmacy Inventory Prediction System
# MODULE: Streamlit Multipage Web Dashboard (app.py)
# DESCRIPTION: A gorgeous, professional, and interactive 7-page dashboard
#             supporting bilingual labels, visual charts, inventory CRUD (Add,
#             Update, Delete), and machine learning predictions.
#
# EXPLAINER FOR BEGINNERS:
# - Multipage Navigation: Implemented using sidebar radio controls to toggle
#   between the 7 pages requested.
# - Responsive Plotly Charts: Used for detailed demand, category, and seasonal analysis.
# - CSV Persistence: CRUD operations are saved in real-time using Pandas .to_csv().
# - Bilingual Support: Handled using translations dictionary indexed by language toggle.
# =====================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Import ML engine functions
from ml_model import load_data, predict_stockout_details, get_season_flags

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Smart Pharmacy Inventory System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Modern Healthcare CSS Styles
st.markdown("""
    <style>
    /* Styling headers & text */
    .main-title {
        color: #004d40;
        font-family: 'Outfit', 'Segoe UI', sans-serif;
        font-weight: 800;
        font-size: 2.3rem;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        color: #00796b;
        font-size: 1.0rem;
        margin-bottom: 1.5rem;
    }
    .page-header {
        color: #004d40;
        font-weight: 700;
        border-bottom: 3px solid #008080;
        padding-bottom: 8px;
        margin-bottom: 20px;
    }
    
    /* Metrics panel cards */
    .metric-card {
        border-radius: 10px;
        padding: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border-left: 5px solid;
        margin-bottom: 10px;
    }
    .metric-green {
        background-color: #e8f5e9;
        border-left-color: #2e7d32;
        color: #1b5e20;
    }
    .metric-yellow {
        background-color: #fffde7;
        border-left-color: #fbc02d;
        color: #f57f17;
    }
    .metric-red {
        background-color: #ffebee;
        border-left-color: #c62828;
        color: #b71c1c;
    }
    
    /* Standardized Buttons */
    .stButton>button {
        background-color: #008080 !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 6px 16px !important;
        font-weight: 600 !important;
    }
    .stButton>button:hover {
        background-color: #004d40 !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.12) !important;
    }
    
    /* Info banners */
    .clinic-banner {
        background-color: #e0f2f1;
        border: 1px solid #b2dfdb;
        border-radius: 8px;
        padding: 12px;
        color: #004d40;
        font-size: 0.95rem;
        margin-bottom: 15px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# BILINGUAL TRANSLATION SYSTEM
# ==========================================
TRANSLATIONS = {
    "English": {
        "title": "Smart Pharmacy Inventory Prediction System",
        "subtitle": "Healthcare AI for Rural Clinics & Small Pharmacies",
        "nav_title": "📋 Navigation Menu",
        "nav_p1": "🏠 Home Dashboard",
        "nav_p2": "📦 Inventory Management",
        "nav_p3": "🔮 Prediction Analytics",
        "nav_p4": "⚠️ Alerts & Risks",
        "nav_p5": "🍂 Seasonal Insights",
        "nav_p6": "📈 Medicine Trends",
        "nav_p7": "📄 Reports & Exports",
        "clinic_badge": "📍 Designed for low-resource primary healthcare centers (PHCs) in India.",
        "metrics_total": "Total Stocked Formulations",
        "metrics_critical": "Critical Life-saving Drugs",
        "metrics_low": "Low Stock (Yellow Warnings)",
        "metrics_urgent": "Urgent Stockout (Red Alerts)",
        "col_med_id": "Medicine ID",
        "col_name": "Medicine Name",
        "col_category": "Therapeutic Category",
        "col_stock": "Current Stock",
        "col_threshold": "Safety Reorder Limit",
        "col_expiry": "Expiry Date",
        "col_critical": "Critical?",
        "col_price": "Unit Price (₹)",
        "col_supplier": "Supplier Name",
        "col_pattern": "Seasonal Pattern",
        "col_risk": "AI Risk Status",
        "col_days": "Days Remaining",
        "col_date": "Est. Stockout Date",
        "search_label": "Search medicine inventory...",
        "filter_category": "Filter by Category",
        "btn_add": "Add Medicine to Database",
        "btn_update": "Update Stock Shelf Qty",
        "btn_delete": "Delete Medicine Permanently",
        "delete_confirm": "Confirm deletion check",
        "ml_select": "Choose Medicine for Demand Simulation",
        "ml_model": "Select Forecast Engine Model",
        "ml_stockout_est": "Estimated Depletion Date",
        "ml_days_left": "Estimated Days of Stock Left",
        "ml_status": "Inventory Status Alert Indicator",
        "ml_metrics": "Model Validation Score (Test Set)",
        "restock_title": "AI Smart Restocking Procurement Orders",
        "col_reorder_qty": "Recommended Order Qty",
        "col_reorder_cost": "Estimated Purchase Bill (₹)",
        "expired": "EXPIRED (Discard Immediately)",
        "expiring_soon": "EXPIRING SOON (< 30 Days)",
        "btn_download_inv": "Download Complete Inventory CSV",
        "btn_download_rec": "Download Restocking Order Sheet CSV"
    },
    "Marathi": {
        "title": "स्मार्ट फार्मसी इन्व्हेंटरी अंदाज प्रणाली",
        "subtitle": "ग्रामीण रुग्णालये आणि लहान औषधालयांसाठी आरोग्य सेवा AI",
        "nav_title": "📋 मुख्य मेनू (Navigation)",
        "nav_p1": "🏠 होम डॅशबोर्ड",
        "nav_p2": "📦 साठा व्यवस्थापन (Inventory)",
        "nav_p3": "🔮 AI मागणी अंदाज (Predictions)",
        "nav_p4": "⚠️ इशारे आणि धोके (Alerts)",
        "nav_p5": "🍂 हंगामी विश्लेषण (Seasonality)",
        "nav_p6": "📈 औषध विक्री प्रवाह (Trends)",
        "nav_p7": "📄 अहवाल आणि निर्यात (Reports)",
        "clinic_badge": "📍 भारतातील ग्रामीण प्राथमिक आरोग्य केंद्रांसाठी (PHC) विशेष रचना.",
        "metrics_total": "एकूण उपलब्ध औषधे",
        "metrics_critical": "अति-महत्त्वाची औषधे संख्या",
        "metrics_low": "कमी साठा असलेली औषधे (पिवळा)",
        "metrics_urgent": "अति-तातडीने खरेदी साठा (लाल)",
        "col_med_id": "औषध कोड",
        "col_name": "औषधाचे नाव",
        "col_category": "औषध प्रकार श्रेणी",
        "col_stock": "सध्याचा उपलब्ध साठा",
        "col_threshold": "सुरक्षित साठा मर्यादा",
        "col_expiry": "कालबाह्यता तारीख",
        "col_critical": "अति-महत्त्वाचे?",
        "col_price": "किंमत (₹)",
        "col_supplier": "वितरकाचे नाव",
        "col_pattern": "हंगामी विक्री प्रकार",
        "col_risk": "AI साठा पातळी स्थिती",
        "col_days": "शिल्लक दिवस",
        "col_date": "अंदाजित साठा संपण्याची तारीख",
        "search_label": "औषध साठा शोधा...",
        "filter_category": "श्रेणीनुसार निवडा",
        "btn_add": "नवीन औषध जोडा",
        "btn_update": "चालू साठा अद्ययावत करा",
        "btn_delete": "औषध कायमचे काढून टाका",
        "delete_confirm": "काढून टाकण्याची पुष्टी करा",
        "ml_select": "मागणी अंदाजासाठी औषध निवडा",
        "ml_model": "निवडा मशीन लर्निंग मॉडेल",
        "ml_stockout_est": "अंदाजित साठा संपण्याची तारीख",
        "ml_days_left": "उर्वरित साठ्याचे अंदाजित दिवस",
        "ml_status": "सध्याची साठा पातळी स्थिती",
        "ml_metrics": "मॉडेल अचूकता विश्लेषण (Test Set)",
        "restock_title": "AI आधारित पुनर्खरेदी शिफारसी पत्र",
        "col_reorder_qty": "शिफारस केलेली खरेदी संख्या",
        "col_reorder_cost": "अंदाजित खरेदी खर्च (₹)",
        "expired": "मुदत संपली आहे (त्वरित नष्ट करा)",
        "expiring_soon": "मुदत लवकरच संपणार आहे (< ३० दिवस)",
        "btn_download_inv": "एकूण साठा अहवाल डाउनलोड करा (CSV)",
        "btn_download_rec": "पुनर्खरेदी शिफारसी डाउनलोड करा (CSV)"
    }
}

# Ensure data sets are initialized
if not os.path.exists("data/medicine_inventory.csv") or not os.path.exists("data/daily_usage_history.csv"):
    from data_generator import generate_datasets
    generate_datasets()

# Load latest working data
inventory, history = load_data()

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.markdown("<h2 style='color:#008080;'>⚙️ Smart System</h2>", unsafe_allow_html=True)

# Bilingual language toggle
lang_toggle = st.sidebar.checkbox("मराठीत पहा / View in Marathi", value=False)
lang = "Marathi" if lang_toggle else "English"
texts = TRANSLATIONS[lang]

st.sidebar.markdown(f"**Bilingual Active:** `{lang}`")
st.sidebar.markdown("---")

# Render 7 Page Sidebar Radio controls
st.sidebar.markdown(f"### {texts['nav_title']}")
page = st.sidebar.radio(
    "",
    [
        texts["nav_p1"],
        texts["nav_p2"],
        texts["nav_p3"],
        texts["nav_p4"],
        texts["nav_p5"],
        texts["nav_p6"],
        texts["nav_p7"]
    ]
)

# Sidebar clinical notes
st.sidebar.markdown("---")
st.sidebar.markdown(f"<div class='clinic-banner'>{texts['clinic_badge']}</div>", unsafe_allow_html=True)

# Render Global Main App headers
st.markdown(f"<div class='main-title'>{texts['title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>{texts['subtitle']}</div>", unsafe_allow_html=True)

# Calculate ML predictions for metrics in real time (Cached for performance)
@st.cache_data(ttl=300)
def get_cached_predictions(model_name="Linear Regression"):
    preds = {}
    for index, row in inventory.iterrows():
        med = row["medicine_name"]
        stk = row["current_stock"]
        preds[med] = predict_stockout_details(med, stk, model_name)
    return preds

ml_results = get_cached_predictions()

# Compile alerts metrics for Home overview
total_meds_count = len(inventory)
critical_meds_count = len(inventory[inventory["is_critical"] == "Yes"])
red_alerts_count = sum(1 for r in ml_results.values() if r["risk_level"] == "RED")
yellow_alerts_count = sum(1 for r in ml_results.values() if r["risk_level"] == "YELLOW")

# ==========================================
# PAGE 1: HOME DASHBOARD
# ==========================================
if page == texts["nav_p1"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p1']}</h3>", unsafe_allow_html=True)
    
    # KPI Metric Card Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class='metric-card' style='background-color:#e0f2f1; border-left-color:#008080; color:#004d40;'>
                <h3>{total_meds_count}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_total']}</b></p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class='metric-card' style='background-color:#e0f7fa; border-left-color:#00bcd4; color:#006064;'>
                <h3>{critical_meds_count}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_critical']}</b></p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class='metric-card metric-yellow'>
                <h3>{yellow_alerts_count}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_low']}</b></p>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class='metric-card metric-red'>
                <h3>{red_alerts_count}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_urgent']}</b></p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Plotly overview chart: stock levels vs minimum required levels
    st.markdown("### 📊 Inventory Stock Status vs Safety Reorder Levels")
    
    inventory["Safety Status"] = [
        "🔴 RED (Urgent)" if ml_results.get(name, {"risk_level": "GREEN"})["risk_level"] == "RED"
        else ("🟡 YELLOW (Low)" if ml_results.get(name, {"risk_level": "GREEN"})["risk_level"] == "YELLOW" else "🟢 GREEN (Safe)")
        for name in inventory["medicine_name"]
    ]
    
    fig_overview = px.bar(
        inventory,
        x="medicine_name",
        y=["current_stock", "min_required_stock"],
        barmode="group",
        labels={"value": "Quantity (Units)", "medicine_name": "Medicine", "variable": "Stock Type"},
        title="Current Shelf Stock compared to Reorder Point",
        color_discrete_sequence=["#008080", "#ff7f0e"]
    )
    fig_overview.update_layout(xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig_overview, use_container_width=True)
    
    # Instruction guide cards for rural operators
    st.markdown("### ℹ️ Rural Clinic System Guidelines")
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.info("""
            💡 **Stock Monitoring instructions:**
            - **Green items** require no action. They hold safe quantities.
            - **Yellow items** indicate you have enough for about 8-15 days. Plan orders this week.
            - **Red items** are critical. Place procurement orders immediately to avoid doctor shortages.
        """)
    with g_col2:
        st.warning("""
            🚨 **Bilingual & Critical Alerts Guide:**
            - Check the **Alerts & Risks** page to see expired medications that must be discarded immediately.
            - High-criticality drugs (Insulin, Salbutamol) will raise separate alarms if they are low.
        """)

# ==========================================
# PAGE 2: INVENTORY MANAGEMENT (CRUD)
# ==========================================
elif page == texts["nav_p2"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p2']}</h3>", unsafe_allow_html=True)
    
    # 1. Main Search & Filter Table
    s_col1, s_col2 = st.columns([2, 1])
    with s_col1:
        query = st.text_input(texts["search_label"], "")
    with s_col2:
        cats = ["All"] + list(inventory["category"].unique())
        selected_cat = st.selectbox(texts["filter_category"], cats)
        
    filtered = inventory.copy()
    if query:
        filtered = filtered[filtered["medicine_name"].str.contains(query, case=False)]
    if selected_cat != "All":
        filtered = filtered[filtered["category"] == selected_cat]
        
    # Inject status details
    filtered["AI Status"] = [
        "🔴 RED" if ml_results.get(name, {"risk_level": "GREEN"})["risk_level"] == "RED"
        else ("🟡 YELLOW" if ml_results.get(name, {"risk_level": "GREEN"})["risk_level"] == "YELLOW" else "🟢 GREEN")
        for name in filtered["medicine_name"]
    ]
    
    rename_cols = {
        "medicine_id": texts["col_med_id"],
        "medicine_name": texts["col_name"],
        "bilingual_name": "मराठी नाव (Bilingual)",
        "category": texts["col_category"],
        "current_stock": texts["col_stock"],
        "min_required_stock": texts["col_threshold"],
        "expiry_date": texts["col_expiry"],
        "is_critical": texts["col_critical"],
        "unit_price": texts["col_price"],
        "supplier_name": texts["col_supplier"],
        "seasonal_demand_pattern": texts["col_pattern"],
        "AI Status": texts["col_risk"]
    }
    
    st.dataframe(filtered.rename(columns=rename_cols), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 2. Add, Update, and Delete forms
    crud_tabs = st.tabs([f"➕ {texts['btn_add']}", f"🔄 {texts['btn_update']}", f"❌ {texts['btn_delete']}"])
    
    # Tab A: Add medicine
    with crud_tabs[0]:
        st.markdown(f"#### {texts['btn_add']}")
        with st.form("add_form", clear_on_submit=True):
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                name_en = st.text_input("Medicine Name (English)", placeholder="e.g. Paracetamol 500mg")
                name_mr = st.text_input("Bilingual Label (Marathi)", placeholder="उदा. पॅरासिटामॉल ५००mg")
                cat = st.selectbox("Category", list(inventory["category"].unique()) + ["Other"])
                stock = st.number_input("Current Stock on Hand", min_value=0, value=120)
                reorder = st.number_input("Reorder Level Threshold", min_value=5, value=25)
            with a_col2:
                exp = st.date_input("Expiry Date", min_value=datetime.today())
                price = st.number_input("Price per unit (₹)", min_value=0.1, value=4.50)
                crit = st.selectbox("Is this medicine critical/life-saving?", ["No", "Yes"])
                supp = st.text_input("Supplier Name", placeholder="e.g. Sahyadri Logistics")
                pattern = st.selectbox("Seasonal Demand Pattern", ["Constant", "Monsoon Spike", "Winter Spike", "Summer Spike"])
                
            submitted_add = st.form_submit_button(texts["btn_add"])
            if submitted_add:
                if not name_en or not name_mr or not supp:
                    st.error("Please fill in all the required text fields.")
                else:
                    new_id = f"MED{len(inventory)+1:03d}"
                    new_row = {
                        "medicine_id": new_id,
                        "medicine_name": name_en,
                        "bilingual_name": name_mr,
                        "category": cat,
                        "current_stock": int(stock),
                        "min_required_stock": int(reorder),
                        "expiry_date": exp.strftime("%Y-%m-%d"),
                        "is_critical": crit,
                        "unit_price": float(price),
                        "supplier_name": supp,
                        "seasonal_demand_pattern": pattern
                    }
                    inventory = pd.concat([inventory, pd.DataFrame([new_row])], ignore_index=True)
                    inventory.to_csv("data/medicine_inventory.csv", index=False)
                    st.success(f"Successfully added medicine: **{name_en}** ({new_id})")
                    st.cache_data.clear()
                    st.rerun()
                    
    # Tab B: Update stock
    with crud_tabs[1]:
        st.markdown(f"#### {texts['btn_update']}")
        with st.form("update_form", clear_on_submit=True):
            select_med = st.selectbox("Select Medicine to Restock/Modify", inventory["medicine_name"].unique())
            current_st = inventory[inventory["medicine_name"] == select_med]["current_stock"].values[0]
            st.info(f"Current count on shelf: **{current_st} units**")
            
            new_qty = st.number_input("New Stock Level Quantity", min_value=0, value=int(current_st))
            submitted_update = st.form_submit_button(texts["btn_update"])
            
            if submitted_update:
                inventory.loc[inventory["medicine_name"] == select_med, "current_stock"] = int(new_qty)
                inventory.to_csv("data/medicine_inventory.csv", index=False)
                st.success(f"Stock quantity successfully updated for: **{select_med}** to **{new_qty} units**")
                st.cache_data.clear()
                st.rerun()

    # Tab C: Delete medicine
    with crud_tabs[2]:
        st.markdown(f"#### {texts['btn_delete']}")
        select_del = st.selectbox("Select Medicine to Delete", inventory["medicine_name"].unique())
        st.warning(f"⚠️ Warning: Deleting **{select_del}** will remove it permanently from database.")
        
        confirm = st.checkbox(texts["delete_confirm"])
        btn_del = st.button(texts["btn_delete"])
        
        if btn_del:
            if not confirm:
                st.error("Please check the 'Confirm deletion' box to execute.")
            else:
                inventory = inventory[inventory["medicine_name"] != select_del]
                inventory.to_csv("data/medicine_inventory.csv", index=False)
                st.success(f"Successfully deleted **{select_del}** permanently.")
                st.cache_data.clear()
                st.rerun()

# ==========================================
# PAGE 3: PREDICTION ANALYTICS
# ==========================================
elif page == texts["nav_p3"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p3']}</h3>", unsafe_allow_html=True)
    
    col_p3_1, col_p3_2 = st.columns([1, 2])
    with col_p3_1:
        st.markdown("### 🛠️ Prediction Setup")
        sel_med_pred = st.selectbox(texts["ml_select"], inventory["medicine_name"].unique())
        sel_model = st.selectbox(texts["ml_model"], ["Linear Regression", "Random Forest Regressor"])
        
        # Details of medicine
        row_det = inventory[inventory["medicine_name"] == sel_med_pred].iloc[0]
        stk_curr = row_det["current_stock"]
        crit_flg = row_det["is_critical"]
        thresh_flg = row_det["min_required_stock"]
        
        st.markdown("---")
        st.markdown(f"**Bilingual Label:** `{row_det['bilingual_name']}`")
        st.markdown(f"**Current Stock Level:** `{stk_curr} units`")
        st.markdown(f"**Reorder Limit:** `{thresh_flg} units`")
        st.markdown(f"**Supplier:** `{row_det['supplier_name']}`")
        st.markdown(f"**Is Critical?:** `{'🔴 YES' if crit_flg == 'Yes' else 'No'}`")
        
        # Run ML engine calculations
        with st.spinner("Training model in real-time..."):
            ml_res = predict_stockout_details(sel_med_pred, stk_curr, sel_model)
            
        days_rem = ml_res["days_left"]
        stout_dt = ml_res["stockout_date"]
        risk_lvl = ml_res["risk_level"]
        acc_metric = ml_res["metrics"]
        
        if risk_lvl == "RED":
            card_html = "<div class='metric-card metric-red' style='text-align:center;'><h4>🚨 RED: Urgent Stockout Risk</h4></div>"
        elif risk_lvl == "YELLOW":
            card_html = "<div class='metric-card metric-yellow' style='text-align:center;'><h4>⚠️ YELLOW: Low Stock Warning</h4></div>"
        else:
            card_html = "<div class='metric-card metric-green' style='text-align:center;'><h4>✅ GREEN: Stock is Safe</h4></div>"
            
        st.markdown(card_html, unsafe_allow_html=True)
        st.markdown(f"""
            <div style='background-color:#f5f5f5; border-radius:8px; padding:10px; font-size:0.85rem;'>
                <p style='margin-bottom:2px;'><b>{texts['ml_metrics']}</b></p>
                <code>{acc_metric}</code>
            </div>
        """, unsafe_allow_html=True)
        
    with col_p3_2:
        st.markdown(f"### 📈 Forecast Timeline: **{sel_med_pred}**")
        
        # Results panels
        k_col1, k_col2 = st.columns(2)
        with k_col1:
            st.metric(texts["ml_stockout_est"], stout_dt)
        with k_col2:
            st.metric(texts["ml_days_left"], f"{days_rem} Days" if days_rem < 900 else "> 30 Days")
            
        # Draw interactive timeline Plotly chart
        hist_df = history[history["medicine_name"] == sel_med_pred].sort_values("date").tail(60) # Last 60 days
        f_df = ml_res["forecast_df"]
        
        fig_timeline = go.Figure()
        
        # History line
        fig_timeline.add_trace(go.Scatter(
            x=hist_df["date"],
            y=hist_df["quantity_used"],
            mode="lines+markers",
            name="Past 60 Days Demand",
            line=dict(color="#1f77b4", width=2)
        ))
        
        # Forecast line
        fig_timeline.add_trace(go.Scatter(
            x=f_df["date"],
            y=f_df["predicted_usage"],
            mode="lines+markers",
            name="AI Predicted Demand (30 Days)",
            line=dict(color="#ff7f0e", width=2, dash="dash")
        ))
        
        fig_timeline.update_layout(
            title=f"Usage Forecast for {sel_med_pred}",
            xaxis_title="Date",
            yaxis_title="Units Dispensed Daily",
            legend=dict(x=0, y=1),
            hovermode="x unified",
            height=380
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # AI explainability for vivas
        st.info("""
            🎓 **Explainability Guideline for Students:**
            - **Linear Regression** uses a standard trend line. It assumes demand increases or decreases uniformly by season.
            - **Random Forest Regressor** uses decision trees to identify complex seasonal peaks (like monsoon fevers).
            - The model features dates, seasonal indicators, and a 7-day rolling sales average to dynamically predict demand.
        """)

# ==========================================
# PAGE 4: ALERTS & RISKS
# ==========================================
elif page == texts["nav_p4"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p4']}</h3>", unsafe_allow_html=True)
    
    # 1. Color-coded alerts list
    st.markdown("### 🚨 Urgent Shortage Alerts (Red & Yellow Risks)")
    
    red_alerts = []
    yellow_alerts = []
    
    for name, res in ml_results.items():
        row_i = inventory[inventory["medicine_name"] == name].iloc[0]
        cur_s = row_i["current_stock"]
        crit_f = row_i["is_critical"]
        sup_n = row_i["supplier_name"]
        
        alert_row = {
            "Medicine Name": name,
            "Marathi Label": row_i["bilingual_name"],
            "Current Stock": cur_s,
            "Days Remaining": res["days_left"] if res["days_left"] < 900 else ">30 Days",
            "Est. Stockout Date": res["stockout_date"],
            "Is Critical?": "Yes 🚨" if crit_f == "Yes" else "No",
            "Supplier Contact": sup_n
        }
        
        if res["risk_level"] == "RED":
            red_alerts.append(alert_row)
        elif res["risk_level"] == "YELLOW":
            yellow_alerts.append(alert_row)
            
    a_tab1, a_tab2 = st.tabs([f"🔴 Urgent Stockouts ({len(red_alerts)})", f"🟡 Low Stock Warnings ({len(yellow_alerts)})"])
    
    with a_tab1:
        if red_alerts:
            st.dataframe(pd.DataFrame(red_alerts), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Fantastic! Zero medicines are in the critical red danger zone.")
            
    with a_tab2:
        if yellow_alerts:
            st.dataframe(pd.DataFrame(yellow_alerts), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Excellent! No low stock warnings logged.")
            
    st.markdown("---")
    
    # 2. Expiry Watchdog Section
    st.markdown("### 📅 Expiry Watchdog & Monitoring")
    
    expired_list = []
    expiring_soon_list = []
    today_dt = datetime.now()
    
    for index, row in inventory.iterrows():
        exp_dt = datetime.strptime(row["expiry_date"], "%Y-%m-%d")
        
        row_exp = {
            "Medicine ID": row["medicine_id"],
            "Medicine Name": row["medicine_name"],
            "Expiry Date": row["expiry_date"],
            "Supplier": row["supplier_name"]
        }
        
        if exp_dt <= today_dt:
            row_exp["Status"] = f"🔴 {texts['expired']}"
            row_exp["Action Required"] = "DISCARD IMMEDIATELY! DO NOT DISPENSE!"
            expired_list.append(row_exp)
        elif today_dt < exp_dt <= (today_dt + timedelta(days=30)):
            row_exp["Status"] = f"🟡 {texts['expiring_soon']}"
            days_diff = (exp_dt - today_dt).days
            row_exp["Action Required"] = f"Expires in {days_diff} days. Dispense quickly or return to supplier."
            expiring_soon_list.append(row_exp)
            
    e_col1, e_col2 = st.columns(2)
    with e_col1:
        st.markdown("#### ❌ Expired Stock (Must Discard)")
        if expired_list:
            st.dataframe(pd.DataFrame(expired_list), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Clear. Zero expired medicines on shelves.")
            
    with e_col2:
        st.markdown("#### ⏳ Expiring Soon (Next 30 Days)")
        if expiring_soon_list:
            st.dataframe(pd.DataFrame(expiring_soon_list), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Clear. No medicines expiring in the next 30 days.")

# ==========================================
# PAGE 5: SEASONAL INSIGHTS
# ==========================================
elif page == texts["nav_p5"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p5']}</h3>", unsafe_allow_html=True)
    
    # Educational Overview
    st.markdown("""
        ### 🌧️ India Epidemiological Disease Seasonality
        Rural primary health centers in India face heavily shifting disease waves based on meteorological variations:
        - **Monsoon (June - September):** Mosquito breeding and waterborne bacteria lead to massive fever, malaria, typhoid, and gastrointestinal infections.
        - **Winter (October - January):** Lower temperatures trigger asthma attacks, acute bronchitis, and winter flus.
        - **Summer (February - May):** Extreme temperatures cause heat strokes and dehydration, requiring high rehydration fluids.
    """)
    
    # Season Bar chart
    st.markdown("---")
    st.markdown("### 📊 Average Daily Usage by Category and Season")
    
    # Group history by category & season
    merged_history = history.merge(inventory[["medicine_name", "category"]], on="medicine_name", how="left")
    avg_seasonal_usage = merged_history.groupby(["category", "season"])["quantity_used"].mean().reset_index()
    
    fig_seasonal = px.bar(
        avg_seasonal_usage,
        x="category",
        y="quantity_used",
        color="season",
        barmode="group",
        labels={"quantity_used": "Avg Daily Units Sold", "category": "Therapeutic Category"},
        title="Seasonal Shift in Medical Consumption Types",
        color_discrete_sequence=["#e67e22", "#2ecc71", "#3498db"]
    )
    fig_seasonal.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig_seasonal, use_container_width=True)
    
    # Highlight seasonal patterns in table
    st.markdown("### 🔍 Highlighted High-Demand Drugs by Season")
    s_select = st.selectbox("Select Season to View High Demand Medicines", ["Monsoon", "Winter", "Summer"])
    
    # Filter medicines matching that season spike
    pattern_map = {"Monsoon": "Monsoon Spike", "Winter": "Winter Spike", "Summer": "Summer Spike"}
    matching_meds = inventory[inventory["seasonal_demand_pattern"] == pattern_map[s_select]]
    
    st.dataframe(matching_meds[[
        "medicine_id", "medicine_name", "bilingual_name", 
        "category", "current_stock", "supplier_name"
    ]], use_container_width=True, hide_index=True)

# ==========================================
# PAGE 6: MEDICINE TRENDS
# ==========================================
elif page == texts["nav_p6"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p6']}</h3>", unsafe_allow_html=True)
    
    # 1. Multi-medicine comparison chart
    st.markdown("### 📊 Multi-Medicine Trend Comparison")
    selected_meds = st.multiselect(
        "Select Medicines to Overlay on Line Graph",
        inventory["medicine_name"].unique(),
        default=["Paracetamol 650mg", "ORS (Oral Rehydration)", "Cough Syrup 100ml"]
    )
    
    if selected_meds:
        # Filter history for selected medicines and aggregate monthly averages
        hist_filtered = history[history["medicine_name"].isin(selected_meds)].copy()
        hist_filtered["date"] = pd.to_datetime(hist_filtered["date"])
        hist_filtered["Year-Month"] = hist_filtered["date"].dt.to_period("M").astype(str)
        
        monthly_avg = hist_filtered.groupby(["medicine_name", "Year-Month"])["quantity_used"].mean().reset_index()
        
        fig_lines = px.line(
            monthly_avg,
            x="Year-Month",
            y="quantity_used",
            color="medicine_name",
            labels={"quantity_used": "Average Daily Quantity Consumed", "Year-Month": "Timeline Month"},
            title="Monthly Consumption Trends (Past Year)",
            markers=True
        )
        st.plotly_chart(fig_lines, use_container_width=True)
    else:
        st.info("Please select one or more medicines above to overlay their demand lines.")
        
    st.markdown("---")
    
    # 2. Category-wise stock allocation chart
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("### 📂 Category Allocation Share")
        cat_shares = inventory.groupby("category")["current_stock"].sum().reset_index()
        fig_shares = px.pie(
            cat_shares,
            values="current_stock",
            names="category",
            title="Current Category Share on Pharmacy Shelves",
            color_discrete_sequence=px.colors.qualitative.Teal
        )
        st.plotly_chart(fig_shares, use_container_width=True)
        
    with t_col2:
        st.markdown("### 📦 Stock Out Risk Heatmap")
        risk_counts = inventory["Safety Status"].value_counts().reset_index()
        risk_counts.columns = ["Safety Level", "Number of Medicines"]
        fig_risk = px.bar(
            risk_counts,
            x="Safety Level",
            y="Number of Medicines",
            color="Safety Level",
            title="Count of Medicines by Safety Alert Level",
            color_discrete_map={"🟢 GREEN (Safe)": "#2e7d32", "🟡 YELLOW (Low)": "#fbc02d", "🔴 RED (Urgent)": "#c62828"}
        )
        st.plotly_chart(fig_risk, use_container_width=True)

# ==========================================
# PAGE 7: REPORTS & EXPORTS
# ==========================================
elif page == texts["nav_p7"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p7']}</h3>", unsafe_allow_html=True)
    
    st.markdown(f"### 📋 {texts['restock_title']}")
    
    # Compile restocking procurement lists
    order_list = []
    for index, row in inventory.iterrows():
        med_name = row["medicine_name"]
        curr_stock = row["current_stock"]
        unit_price = row["unit_price"]
        is_crit = row["is_critical"]
        sup_n = row["supplier_name"]
        
        res = ml_results.get(med_name)
        if res and not res["forecast_df"].empty:
            forecast_df = res["forecast_df"]
            total_30_day_demand = forecast_df["predicted_usage"].sum()
            
            # Reorder buffer: 30 day demand + 8 day safety margin - current stock
            safety_buffer = int(round(forecast_df["predicted_usage"].mean() * 8))
            recommended_reorder = max(0, int(total_30_day_demand + safety_buffer - curr_stock))
            estimated_cost = round(recommended_reorder * unit_price, 2)
            
            if recommended_reorder > 0:
                order_list.append({
                    "Medicine ID": row["medicine_id"],
                    "Medicine Name": med_name,
                    "Marathi Name": row["bilingual_name"],
                    "Is Critical?": "Yes 🚨" if is_crit == "Yes" else "No",
                    "Supplier Contact": sup_n,
                    "Current Stock": curr_stock,
                    "Recommended Order Qty": recommended_reorder,
                    "Est 30-Day Demand": int(total_30_day_demand),
                    "Unit Cost (₹)": unit_price,
                    "Estimated Bill (₹)": estimated_cost
                })
                
    if order_list:
        order_df = pd.DataFrame(order_list)
        
        # Sort critical items on top
        order_df["sort_crit"] = order_df["Is Critical?"].apply(lambda x: 1 if "Yes" in x else 0)
        order_df = order_df.sort_values(by=["sort_crit", "Estimated Bill (₹)"], ascending=[False, False]).drop(columns=["sort_crit"])
        
        st.dataframe(order_df, use_container_width=True, hide_index=True)
        
        # Procurement Summary Box
        st.markdown("---")
        total_proc_cost = order_df["Estimated Bill (₹)"].sum()
        total_order_qty = order_df["Recommended Order Qty"].sum()
        
        sum1, sum2 = st.columns(2)
        with sum1:
            st.metric("Total Procurement Order Units", f"{total_order_qty} units")
        with sum2:
            st.metric("Total procurement Estimate Cost (₹)", f"₹{total_proc_cost:,.2f}")
            
        # Download reports block
        st.markdown("### 📥 Downloadable CSV Reports")
        down_col1, down_col2 = st.columns(2)
        with down_col1:
            # Download complete shelf stock
            csv_inv = inventory.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=texts["btn_download_inv"],
                data=csv_inv,
                file_name="medicine_inventory_report.csv",
                mime="text/csv"
            )
        with down_col2:
            # Download purchase order sheet
            csv_rec = order_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=texts["btn_download_rec"],
                data=csv_rec,
                file_name="ai_procurement_order_sheet.csv",
                mime="text/csv"
            )
            
        # Mockup PDF text printout for copy-pasting
        st.markdown("### 📝 Official Clinic Procurement Report (Text Format)")
        report_text = f"""=====================================================================
OFFICIAL CLINIC PROCUREMENT REPORT (AI AUTOGENERATED)
GENERATED ON: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
RURAL PHC CLINIC PORTAL - INDIA
=====================================================================
TOTAL ORDER ITEMS  : {total_order_qty} units
ESTIMATED COST      : INR {total_proc_cost:,.2f}
ORDER BREAKDOWN:
"""
        for _, r in order_df.iterrows():
            report_text += f"- {r['Medicine Name']} ({r['Marathi Name']}) | Qty: {r['Recommended Order Qty']} units | Cost: ₹{r['Estimated Bill (₹)']} | Supplier: {r['Supplier Contact']}\n"
        
        st.text_area("", report_text, height=250)
        
    else:
        st.success("✅ All medicines are fully stocked! No procurement order needed at this time.")
