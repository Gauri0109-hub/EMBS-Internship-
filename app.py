# =====================================================================
# PROJECT: Enterprise Pharmacy AI Platform
# MODULE: Upgraded Main Application Wrapper (app.py)
# DESCRIPTION: Streamlit frontend web app rendering the 8 production pages:
#             Dashboard, Inventory CRUD, spreadsheet Data Uploads, Predictions,
#             Alerts watch, Supplier registry, Reports center, and secure Sign Up.
#
# EXPLAINER FOR BEGINNERS:
# - Multipage Navigation: Uses st.sidebar.radio to seamlessly direct users
#   to 8 highly professional, secure pages.
# - SQLite RELATIONAL SYSTEM: All reads and writes target the 10 synchronized SQL tables
#   (tenants, branches, users, suppliers, medicines, inventory, sales_history, etc.).
# - Password Hashing: Uses SHA-256 for user creation during interactive Sign Up.
# =====================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sqlite3

# Import Database Connector & Services
from database.db_manager import initialize_database, get_connection, hash_password
from services.auth_service import show_login_interface, verify_role_access
from services.ingestion_service import (
    validate_inventory_upload, validate_sales_upload,
    import_inventory_to_db, import_sales_to_db
)
from services.procurement_service import calculate_reorder_points
from services.ml_service import train_ensemble_and_select_best, generate_forecast_30_days

# Boot up database tables on first launch
initialize_database()

# Set Page Config
st.set_page_config(
    page_title="Smart Pharmacy Platform",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Healthcare Styling via CSS injection
st.markdown("""
    <style>
    /* Styling headers & texts */
    .main-title {
        color: #004d40;
        font-family: 'Outfit', 'Segoe UI', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        color: #00796b;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    .page-header {
        color: #004d40;
        font-weight: 700;
        border-bottom: 3px solid #008080;
        padding-bottom: 6px;
        margin-bottom: 18px;
    }
    
    /* Metrics blocks */
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
    .metric-blue {
        background-color: #e0f2f1;
        border-left-color: #008080;
        color: #004d40;
    }
    
    /* Buttons and controls */
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
    
    .clinic-banner {
        background-color: #e0f2f1;
        border: 1px solid #b2dfdb;
        border-radius: 8px;
        padding: 10px;
        color: #004d40;
        font-size: 0.9rem;
        margin-bottom: 12px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# BILINGUAL TRANSLATION SYSTEM
# ==========================================
TRANSLATIONS = {
    "English": {
        "title": "Smart Pharmacy Management Platform",
        "subtitle": "Enterprise Healthcare AI Portal - Multi-Tenant Platform",
        "nav_title": "📋 Navigation Menu",
        "nav_p1": "🏠 Home Dashboard",
        "nav_p2": "📦 Inventory Management",
        "nav_p3": "📥 Data Ingest Upload",
        "nav_p4": "🔮 AI Predictions",
        "nav_p5": "⚠️ Alerts & Risks",
        "nav_p6": "🤝 Supplier Registry",
        "nav_p7": "📄 Reports & Exports",
        "nav_p8": "⚙️ Clinic Setup / Sign Up",
        "clinic_badge": "📍 Enterprise Clinic Portal | Synced with SQLite Relational DB.",
        "metrics_total": "Total Medicines Cataloged",
        "metrics_critical": "Critical Stock Items",
        "metrics_low": "Low Stock Warnings",
        "metrics_urgent": "Urgent Stockouts",
        "search_label": "Search Inventory...",
        "filter_category": "Filter by Category",
        "btn_add": "Add Medicine",
        "btn_update": "Update Stock",
        "btn_delete": "Delete Medicine",
        "btn_download_inv": "Download Inventory CSV",
        "btn_download_rec": "Download Restock Orders CSV"
    },
    "Marathi": {
        "title": "स्मार्ट फार्मसी व्यवस्थापन प्लॅटफॉर्म",
        "subtitle": "एंटरप्राइझ हेल्थकेअर एआय पोर्टल - बहु-भाडेकरू प्रणाली",
        "nav_title": "📋 मुख्य मेनू (Navigation)",
        "nav_p1": "🏠 होम डॅशबोर्ड",
        "nav_p2": "📦 औषध साठा व्यवस्थापन",
        "nav_p3": "📥 डेटा आयात व संकलन",
        "nav_p4": "🔮 एआय मागणी अंदाज (ML)",
        "nav_p5": "⚠️ इशारे आणि धोके (Alerts)",
        "nav_p6": "🤝 औषध वितरक नोंदणी",
        "nav_p7": "📄 अहवाल आणि निर्यात (Reports)",
        "nav_p8": "⚙️ नवीन क्लिनिक नोंदणी (Sign Up)",
        "clinic_badge": "📍 बहु-भाडेकरू क्लिनिक पोर्टल | SQLite डेटाबेस कनेक्ट.",
        "metrics_total": "एकूण औषधे नोंदणी संख्या",
        "metrics_critical": "अति-महत्त्वाची औषधे",
        "metrics_low": "कमी साठा इशारे (पिवळा)",
        "metrics_urgent": "अति-तातडीने खरेदी साठा (लाल)",
        "search_label": "साठा शोधा...",
        "filter_category": "श्रेणीनुसार निवडा",
        "btn_add": "नवीन औषध जोडा",
        "btn_update": "चालू साठा अद्ययावत करा",
        "btn_delete": "औषध काढून टाका",
        "btn_download_inv": "एकूण साठा अहवाल (CSV)",
        "btn_download_rec": "पुनर्खरेदी शिफारसी अहवाल (CSV)"
    }
}

# ==========================================
# SECURE LOGIN ROUTER
# ==========================================
if "user" not in st.session_state:
    st.markdown("<div class='main-title'>🩺 Smart Pharmacy AI Platform</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Enterprise Healthcare Inventory Prediction Systems</div>", unsafe_allow_html=True)
    show_login_interface()
    st.stop()

# Load login properties
user = st.session_state.user
tenant_id = user["tenant_id"]
branch_id = user["branch_id"]

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.markdown(f"<h3 style='color:#008080; margin-bottom:2px;'>🩺 {user['tenant_name']}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"📍 **Branch:** `{user['branch_name']}`")
st.sidebar.markdown(f"👤 **User:** `{user['full_name']} ({user['role']})`")

# Logout button
if st.sidebar.button("Logout / लॉगआउट"):
    del st.session_state["user"]
    st.cache_data.clear()
    st.rerun()
    
st.sidebar.markdown("---")

# Bilingual switch
lang_toggle = st.sidebar.checkbox("मराठीत पहा / View in Marathi", value=False)
lang = "Marathi" if lang_toggle else "English"
texts = TRANSLATIONS[lang]

# 8 Upgraded Page Sidebar Radio Selector
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
        texts["nav_p7"],
        texts["nav_p8"]
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"<div class='clinic-banner'>{texts['clinic_badge']}</div>", unsafe_allow_html=True)

# Main Title Headers
st.markdown(f"<div class='main-title'>{texts['title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>{texts['subtitle']}</div>", unsafe_allow_html=True)

# Fetch dynamic warning metrics from relational database
reorder_proc_suggestions = calculate_reorder_points(branch_id, tenant_id)
count_red = sum(1 for r in reorder_proc_suggestions if "OUT OF STOCK" in r["Status"])
count_yellow = sum(1 for r in reorder_proc_suggestions if "Low Stock" in r["Status"])

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM medicines WHERE tenant_id = ?;", (tenant_id,))
tot_meds = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM medicines WHERE tenant_id = ? AND is_critical = 1;", (tenant_id,))
tot_crit = cursor.fetchone()[0]
conn.close()

# ==========================================
# PAGE 1: HOME DASHBOARD
# ==========================================
if page == texts["nav_p1"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p1']}</h3>", unsafe_allow_html=True)
    
    # 4 KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class='metric-card metric-blue'>
                <h3>{tot_meds}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_total']}</b></p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class='metric-card' style='background-color:#e0f7fa; border-left-color:#00bcd4; color:#006064;'>
                <h3>{tot_crit}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_critical']}</b></p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class='metric-card metric-yellow'>
                <h3>{count_yellow}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_low']}</b></p>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class='metric-card metric-red'>
                <h3>{count_red}</h3>
                <p style='margin-bottom:0;'><b>{texts['metrics_urgent']}</b></p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Active Stock Timeline graph
    st.markdown("### 📊 Active Usable Shelf Stock vs Safety Threshold Levels")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.medicine_name, m.min_required_stock,
               (SELECT COALESCE(SUM(b.quantity_stocked), 0) 
                FROM inventory b 
                WHERE b.medicine_id = m.medicine_id AND b.branch_id = ? AND b.expiry_date > DATE('now')) as usable_stock
        FROM medicines m
        WHERE m.tenant_id = ?;
    """, (branch_id, tenant_id))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        df_stock = pd.DataFrame([{
            "Medicine": r["medicine_name"],
            "Usable Stock": r["usable_stock"],
            "Safety Threshold": r["min_required_stock"] if r["min_required_stock"] else 20
        } for r in rows])
        
        fig_stock = px.bar(
            df_stock,
            x="Medicine",
            y=["Usable Stock", "Safety Threshold"],
            barmode="group",
            labels={"value": "Quantity (Units)", "variable": "Stock Type"},
            color_discrete_sequence=["#008080", "#ff9800"]
        )
        fig_stock.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig_stock, use_container_width=True)
    else:
        st.info("No medicine records seeded. Go to 'Data Ingest Upload' to bulk import or add formulations.")

# ==========================================
# PAGE 2: INVENTORY MANAGEMENT (CRUD)
# ==========================================
elif page == texts["nav_p2"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p2']}</h3>", unsafe_allow_html=True)
    
    # Pull medicines and batches dynamically from SQLite
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.medicine_id, m.medicine_name, m.bilingual_name, m.category, m.is_critical, m.unit_price,
               m.min_required_stock, s.supplier_name,
               (SELECT COALESCE(SUM(b.quantity_stocked), 0) FROM inventory b WHERE b.medicine_id = m.medicine_id AND b.branch_id = ?) as total_stock,
               (SELECT COALESCE(SUM(b.quantity_stocked), 0) FROM inventory b WHERE b.medicine_id = m.medicine_id AND b.branch_id = ? AND b.expiry_date > DATE('now')) as usable_stock
        FROM medicines m
        LEFT JOIN suppliers s ON m.preferred_supplier_id = s.supplier_id
        WHERE m.tenant_id = ?;
    """, (branch_id, branch_id, tenant_id))
    meds_rows = cursor.fetchall()
    conn.close()
    
    if meds_rows:
        df_meds = pd.DataFrame([{
            "ID": f"MED{r['medicine_id']:03d}",
            "Medicine Name": r["medicine_name"],
            "Bilingual Label": r["bilingual_name"],
            "Category": r["category"],
            "Total Shelf Stock": r["total_stock"],
            "Usable Stock (Unexpired)": r["usable_stock"],
            "Min Safety Level": r["min_required_stock"],
            "Unit Price (₹)": r["unit_price"],
            "Preferred Supplier": r["supplier_name"] if r["supplier_name"] else "Unassigned",
            "Is Critical?": "Yes 🚨" if r["is_critical"] == 1 else "No",
            "id_raw": r["medicine_id"]
        } for r in meds_rows])
        
        # Search parameters
        s_col1, s_col2 = st.columns([2, 1])
        with s_col1:
            q_term = st.text_input("🔍 Search Medicine Inventory", "")
        with s_col2:
            cat_choices = ["All"] + list(df_meds["Category"].unique())
            sel_category = st.selectbox("📁 Filter Category", cat_choices)
            
        df_filtered_meds = df_meds.copy()
        if q_term:
            df_filtered_meds = df_filtered_meds[df_filtered_meds["Medicine Name"].str.contains(q_term, case=False)]
        if sel_category != "All":
            df_filtered_meds = df_filtered_meds[df_filtered_meds["Category"] == sel_category]
            
        st.dataframe(df_filtered_meds.drop(columns=["id_raw"]), use_container_width=True, hide_index=True)
    else:
        df_filtered_meds = pd.DataFrame()
        st.warning("No medicines active in this tenant branch database.")
        
    # Enforce clear modify clearances
    has_modify_access = verify_role_access(["Admin", "Manager"])
    
    if has_modify_access:
        st.markdown("---")
        st.markdown("### 🔄 Edit Clinic Database Records")
        crud_tabs = st.tabs(["➕ Add New Medicine", "📝 Edit Medicine / Minimum Stock", "❌ Delete Medicine", "🔄 Record incoming Batch"])
        
        # 1. Add Medicine
        with crud_tabs[0]:
            st.markdown("#### Register New Medicine Formulation")
            with st.form("add_med_form", clear_on_submit=True):
                a_name = st.text_input("Medicine Name (English)*", placeholder="e.g. Salbutamol Inhaler")
                a_mr = st.text_input("Bilingual Label (Marathi)*", placeholder="उदा. साल्ब्युटामॉल इनहेलर")
                a_cat = st.text_input("Therapeutic Category*", placeholder="e.g. Respiratory")
                a_price = st.number_input("Unit Price (₹)", min_value=0.1, value=5.0)
                a_min = st.number_input("Minimum Stock Threshold Level", min_value=5, value=20)
                a_crit = st.selectbox("Is this medicine life-saving / critical?", ["No", "Yes"])
                
                # Fetch suppliers to select
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT supplier_id, supplier_name FROM suppliers WHERE tenant_id = ?;", (tenant_id,))
                supps = cursor.fetchall()
                conn.close()
                
                supp_dict = {row["supplier_name"]: row["supplier_id"] for row in supps}
                a_supp = st.selectbox("Preferred Supplier Link", ["None"] + list(supp_dict.keys()))
                
                submitted_add = st.form_submit_button("ADD FORMULATION")
                if submitted_add:
                    if not a_name or not a_mr or not a_cat:
                        st.error("Please fill in all starred inputs.")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        try:
                            pref_id = supp_dict.get(a_supp)
                            cursor.execute("""
                                INSERT INTO medicines (tenant_id, medicine_name, bilingual_name, category, unit_price, is_critical, preferred_supplier_id, min_required_stock)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                            """, (tenant_id, a_name, a_mr, a_cat, a_price, 1 if a_crit == "Yes" else 0, pref_id, a_min))
                            conn.commit()
                            st.success(f"Added **{a_name}** successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("A medicine with this name already exists in your database.")
                        finally:
                            conn.close()
                            
        # 2. Edit Medicine
        with crud_tabs[1]:
            if not df_filtered_meds.empty:
                st.markdown("#### Modify Medicine Properties")
                with st.form("edit_med_form"):
                    select_edit_med = st.selectbox("Select Medicine to Edit", df_filtered_meds["Medicine Name"].unique())
                    row_edit = df_filtered_meds[df_filtered_meds["Medicine Name"] == select_edit_med].iloc[0]
                    
                    e_name = st.text_input("Medicine Name (English)", value=row_edit["Medicine Name"])
                    e_mr = st.text_input("Bilingual Label (Marathi)", value=row_edit["Bilingual Label"])
                    e_cat = st.text_input("Category", value=row_edit["Category"])
                    e_price = st.number_input("Unit Price (₹)", min_value=0.1, value=float(row_edit["Unit Price (₹)"]))
                    e_min = st.number_input("Minimum Stock Level Limit", min_value=5, value=int(row_edit["Min Safety Level"]))
                    e_crit = st.selectbox("Is Critical?", ["No", "Yes"], index=1 if "Yes" in row_edit["Is Critical?"] else 0)
                    
                    # Suppliers
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT supplier_id, supplier_name FROM suppliers WHERE tenant_id = ?;", (tenant_id,))
                    supps = cursor.fetchall()
                    conn.close()
                    supp_dict = {row["supplier_name"]: row["supplier_id"] for row in supps}
                    
                    default_supp_name = row_edit["Preferred Supplier"]
                    e_supp = st.selectbox(
                        "Preferred Supplier", 
                        ["None"] + list(supp_dict.keys()), 
                        index=list(supp_dict.keys()).index(default_supp_name)+1 if default_supp_name in supp_dict else 0
                    )
                    
                    submitted_edit = st.form_submit_button("SAVE MODIFIED PROPERTIES")
                    if submitted_edit:
                        conn = get_connection()
                        cursor = conn.cursor()
                        pref_id = supp_dict.get(e_supp)
                        cursor.execute("""
                            UPDATE medicines
                            SET medicine_name = ?, bilingual_name = ?, category = ?, unit_price = ?, 
                                is_critical = ?, preferred_supplier_id = ?, min_required_stock = ?
                            WHERE medicine_id = ? AND tenant_id = ?;
                        """, (e_name, e_mr, e_cat, e_price, 1 if e_crit == "Yes" else 0, pref_id, e_min, int(row_edit["id_raw"]), tenant_id))
                        conn.commit()
                        conn.close()
                        st.success("Successfully modified properties!")
                        st.rerun()
            else:
                st.write("No medicine catalog records to edit.")
                
        # 3. Delete Medicine
        with crud_tabs[2]:
            if not df_filtered_meds.empty:
                st.markdown("#### Remove Formulation from Database")
                select_del_med = st.selectbox("Choose Medicine to Delete", df_filtered_meds["Medicine Name"].unique())
                del_confirm = st.checkbox("Confirm permanent deletion of formulation and all its batch inventory")
                btn_delete_exe = st.button("DELETE FORMULATION")
                
                if btn_delete_exe:
                    if not del_confirm:
                        st.error("Please check the confirmation box.")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM medicines WHERE medicine_name = ? AND tenant_id = ?;", (select_del_med, tenant_id))
                        conn.commit()
                        conn.close()
                        st.success(f"Permanently deleted **{select_del_med}** from database.")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.write("No medicine catalog records to delete.")
                
        # 4. Record Incoming Batch
        with crud_tabs[3]:
            if not df_filtered_meds.empty:
                st.markdown("#### Log Incoming Supply Shipment Batch")
                with st.form("incoming_batch_form", clear_on_submit=True):
                    sel_batch_med = st.selectbox("Select Medicine Received", df_filtered_meds["Medicine Name"].unique())
                    med_id_raw = df_filtered_meds[df_filtered_meds["Medicine Name"] == sel_batch_med]["id_raw"].values[0]
                    
                    b_num = st.text_input("Batch Number / लॉट नंबर", placeholder="e.g. BAT-2026B")
                    b_qty = st.number_input("Quantity Received (Units)", min_value=1, value=100)
                    b_exp = st.date_input("Expiry Date", min_value=datetime.today())
                    
                    submitted_batch = st.form_submit_button("LOG BATCH")
                    if submitted_batch:
                        if not b_num:
                            st.error("Please enter a valid Batch Number.")
                        else:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO inventory (medicine_id, branch_id, batch_number, quantity_stocked, expiry_date)
                                VALUES (?, ?, ?, ?, ?);
                            """, (int(med_id_raw), branch_id, b_num, int(b_qty), b_exp.strftime("%Y-%m-%d")))
                            conn.commit()
                            conn.close()
                            st.success(f"Log incoming supply: logged batch **{b_num}** successfully!")
                            st.cache_data.clear()
                            st.rerun()
            else:
                st.write("No medicine catalog records to log batches.")
    else:
        st.info("ℹ️ Managers and Admins hold full clearance to edit catalog records and log incoming batches. Your Pharmacist session is restricted to read-only.")

# ==========================================
# PAGE 3: DATA INGEST UPLOAD
# ==========================================
elif page == texts["nav_p3"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p3']}</h3>", unsafe_allow_html=True)
    
    # Ingestion restrictions check
    has_modify_access = verify_role_access(["Admin", "Manager"])
    if not has_modify_access:
        st.warning("⚠️ Access Denied: Bulk spreadsheet importing requires Manager or Admin clearance level.")
    else:
        st.markdown("""
            Upload your Excel (`.xlsx`) or CSV files here. The system cleanses dates, strips negative values,
            and validates schema columns automatically.
        """)
        
        # Download templates section
        st.markdown("#### 📄 1. Download Standard Templates")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            template_inv = pd.DataFrame([{
                "Medicine Name": "Salbutamol Inhaler",
                "Current Stock": 150,
                "Expiry Date": "2027-12-31",
                "Category": "Respiratory",
                "Supplier": "Cipla Healthcare Depot",
                "Critical Medicine Flag": "Yes"
            }])
            st.download_button(
                label="Download Inventory Template CSV",
                data=template_inv.to_csv(index=False).encode('utf-8'),
                file_name="inventory_template.csv",
                mime="text/csv"
            )
        with t_col2:
            template_sales = pd.DataFrame([{
                "Date": "2026-05-31",
                "Medicine Name": "Salbutamol Inhaler",
                "Quantity Sold": 12
            }])
            st.download_button(
                label="Download Sales History Template CSV",
                data=template_sales.to_csv(index=False).encode('utf-8'),
                file_name="sales_history_template.csv",
                mime="text/csv"
            )
            
        # File Upload widgets
        st.markdown("---")
        st.markdown("#### 📂 2. Select Spreadsheet File to Ingest")
        
        upload_type = st.selectbox("Select Upload Dataset Type", ["Inventory Upload (Medicines & Batches)", "Usage History Upload (Sales Transactions)"])
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
        
        if uploaded_file:
            filename = uploaded_file.name
            
            with st.spinner("Processing Ingestion Validation Pipeline..."):
                if "Inventory" in upload_type:
                    report = validate_inventory_upload(uploaded_file, filename)
                else:
                    report = validate_sales_upload(uploaded_file, filename)
                    
            st.markdown("#### 🔬 3. Resilient Ingestion Validation Report")
            if report["status"] == "error":
                st.error("🔴 Ingestion Blocked: The uploaded file has fatal schema errors.")
                for err in report["errors"]:
                    st.write(f"- {err}")
            else:
                st.success(f"🟢 Schema Validated Successfully! Read **{report['records_count']} rows**.")
                
                # Preview Table
                st.markdown("##### 📝 Ingestion Preview (First 10 Rows)")
                st.dataframe(report["preview"], use_container_width=True)
                
                # Warnings List
                if report["warnings"]:
                    with st.expander(f"⚠️ Cleansing & Quality Warnings ({len(report['warnings'])})"):
                        for warn in report["warnings"][:20]:
                            st.warning(warn)
                        if len(report["warnings"]) > 20:
                            st.write(f"... and {len(report['warnings'])-20} more warnings.")
                            
                # Confirm Import Button
                st.markdown("##### 💾 4. Commit Clean Records to SQLite Database")
                btn_commit = st.button("CONFIRM AND IMPORT INTO DATABASE")
                if btn_commit:
                    with st.spinner("Writing records to SQLite tables..."):
                        if "Inventory" in upload_type:
                            success, count = import_inventory_to_db(
                                report["cleansed_df"], tenant_id, branch_id, filename, user["username"]
                            )
                        else:
                            success, count = import_sales_to_db(
                                report["cleansed_df"], tenant_id, branch_id, filename, user["username"]
                            )
                            
                    if success:
                        st.success(f"🏆 Successfully imported **{count} records** into your branch relational database!")
                        st.cache_data.clear() # Clear cache to retrain predictions
                        st.rerun()
                    else:
                        st.error("Error writing records to SQLite table transactions. Rollback executed.")
                        
        # Ingestion Logs history
        st.markdown("---")
        st.markdown("#### 📜 Ingestion Import History Logs")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT upload_date, filename, records_imported, uploaded_by 
            FROM uploads 
            WHERE tenant_id = ? AND branch_id = ?
            ORDER BY upload_date DESC;
        """, (tenant_id, branch_id))
        logs = cursor.fetchall()
        conn.close()
        
        if logs:
            df_logs = pd.DataFrame([{
                "Timestamp": l["upload_date"],
                "Filename": l["filename"],
                "Records Ingested": l["records_imported"],
                "Operator User": l["uploaded_by"]
            } for l in logs])
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.write("No historical bulk spreadsheet imports logged for this branch.")

# ==========================================
# PAGE 4: ML PREDICTIONS
# ==========================================
elif page == texts["nav_p4"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p4']}</h3>", unsafe_allow_html=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT medicine_id, medicine_name FROM medicines WHERE tenant_id = ?;", (tenant_id,))
    choices_med = {row["medicine_name"]: row["medicine_id"] for row in cursor.fetchall()}
    conn.close()
    
    if choices_med:
        col_p3_1, col_p3_2 = st.columns([1, 2])
        with col_p3_1:
            st.markdown("### 🛠️ Forecast Configuration")
            sel_med_name = st.selectbox("Choose Medicine to Model", list(choices_med.keys()))
            sel_med_id = choices_med[sel_med_name]
            
            # Pull unexpired usable stock
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(quantity_stocked), 0) 
                FROM inventory 
                WHERE medicine_id = ? AND branch_id = ? AND expiry_date > DATE('now');
            """, (sel_med_id, branch_id))
            usable_stock = cursor.fetchone()[0]
            conn.close()
            
            st.markdown("---")
            st.write(f"**Usable Shelf Stock:** `{usable_stock} units` *(Expired stock excluded)*")
            
            # ML training
            with st.spinner("Auto Ensemble training LR, Random Forest and Gradient Boosting..."):
                res_ml, err, status_str = train_ensemble_and_select_best(sel_med_id, branch_id)
                
            if err:
                st.warning(f"⚠️ {status_str}")
                st.info("Tip: Bulk import sales spreadsheets in 'Data Ingest Upload' tab to unlock forecasting features.")
                forecast_df = pd.DataFrame()
            else:
                st.markdown(f"""
                    <div style='background-color:#e0f2f1; border-left: 5px solid #008080; border-radius: 8px; padding: 12px; font-size: 0.9rem; color: #004d40;'>
                        <p style='margin:0;'>🥇 <b>Best Model Selected:</b> {res_ml['best_model_name']}</p>
                        <p style='margin:4px 0 0 0; font-size:0.8rem; font-family: monospace;'>{res_ml['metrics']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Stock-out simulation
                forecast_df = generate_forecast_30_days(
                    sel_med_id, branch_id, res_ml["trained_model"], res_ml["features"], res_ml["timeline_df"]
                )
                
                temp_stk = usable_stock
                days_left = 999
                stockout_date = "Safe (>30 Days)"
                
                if temp_stk == 0:
                    days_left = 0
                    stockout_date = datetime.now().strftime("%Y-%m-%d")
                else:
                    for idx, r in forecast_df.iterrows():
                        temp_stk -= r["predicted_usage"]
                        if temp_stk <= 0:
                            days_left = idx + 1
                            stockout_date = r["date"]
                            break
                            
                # Determine risk level
                if days_left <= 5:
                    alert_class = "metric-red"
                    alert_lbl = "🚨 Critical Risk - Immediate Action!"
                elif days_left <= 12:
                    alert_class = "metric-yellow"
                    alert_lbl = "⚠️ Moderate Risk - Reorder Soon"
                else:
                    alert_class = "metric-green"
                    alert_lbl = "✅ Safe Stock Levels"
                    
                st.markdown(f"""
                    <div class='metric-card {alert_class}' style='text-align:center; margin-top: 15px;'>
                        <h4 style='margin:0;'>{alert_lbl}</h4>
                    </div>
                """, unsafe_allow_html=True)
                
                # Explainable AI Weights
                st.markdown("---")
                st.markdown("### 🔮 Explainable AI (XAI) Demand Drivers")
                df_xai = pd.DataFrame([{"Feature": k.replace('_', ' ').title(), "Impact (%)": v} for k, v in res_ml["xai"].items()])
                df_xai = df_xai.sort_values(by="Impact (%)", ascending=True)
                
                fig_xai = px.bar(
                    df_xai,
                    x="Impact (%)",
                    y="Feature",
                    orientation="h",
                    title="Feature Contribution to Demand Prediction",
                    color_discrete_sequence=["#008080"]
                )
                st.plotly_chart(fig_xai, use_container_width=True)
                
        with col_p3_2:
            if not forecast_df.empty:
                st.markdown(f"### 📈 Forecast Timeline Dashboard: **{sel_med_name}**")
                
                col_kpi1, col_kpi2 = st.columns(2)
                with col_kpi1:
                    st.metric("Estimated Depletion Date", stockout_date)
                with col_kpi2:
                    st.metric("Days of Stock Left", f"{days_left} Days" if days_left < 900 else "> 30 Days")
                    
                # Timeline plot
                hist_tail = res_ml["timeline_df"].tail(45)
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=hist_tail["date"],
                    y=hist_tail["quantity_sold"],
                    mode="lines+markers",
                    name="Past Usage (Units)",
                    line=dict(color="#1f77b4", width=2)
                ))
                fig_timeline.add_trace(go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["predicted_usage"],
                    mode="lines+markers",
                    name="Forecast Demand (Units)",
                    line=dict(color="#ff7f0e", width=2, dash="dash")
                ))
                fig_timeline.update_layout(
                    xaxis_title="Timeline Date",
                    yaxis_title="Units Dispensed Daily",
                    legend=dict(x=0, y=1),
                    hovermode="x unified",
                    height=360
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                st.info("""
                    💡 **Explainability Note for Clinicians:**
                    - The blue line shows real sales history. The orange line is what the AI predicts.
                    - If the contribution percentage for 'Rolling Avg' is high, the model is weighting recent consumption speed heavily.
                    - If 'Is Monsoon' is high, the model has identified a seasonal epidemic trigger for this formulation.
                """)
    else:
        st.warning("No medicines active in this branch database.")

# ==========================================
# PAGE 5: ALERTS & RISKS
# ==========================================
elif page == texts["nav_p5"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p5']}</h3>", unsafe_allow_html=True)
    
    # 4-tier alert monitoring
    st.markdown("### 🚨 Relational Warnings & Safety Alarms")
    
    # Compile 4 tiers
    tier_critical = []
    tier_high = []
    tier_medium = []
    tier_low = []
    
    for r in reorder_proc_suggestions:
        row_alert = {
            "Medicine Name": r["Medicine Name"],
            "Usable Stock": r["Usable Stock"],
            "Safety ROP": r["Reorder Point (ROP)"],
            "Recommended Order Qty": r["Recommended Qty"],
            "Supplier": r["Supplier Name"]
        }
        
        status = r["Status"]
        if "OUT OF STOCK" in status:
            row_alert["Severity"] = "🔴 Critical"
            tier_critical.append(row_alert)
        elif "Low Stock" in status:
            row_alert["Severity"] = "🟠 High"
            tier_high.append(row_alert)
            
    # Also parse expiries to compile Medium and Low alerts
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.medicine_name, b.batch_number, b.quantity_stocked, b.expiry_date
        FROM inventory b
        JOIN medicines m ON b.medicine_id = m.medicine_id
        WHERE m.tenant_id = ? AND b.branch_id = ?
        ORDER BY b.expiry_date ASC;
    """, (tenant_id, branch_id))
    batches = cursor.fetchall()
    conn.close()
    
    today_dt = datetime.now().date()
    for b in batches:
        exp_date = datetime.strptime(b["expiry_date"], "%Y-%m-%d").date()
        row_exp = {
            "Medicine Name": b["medicine_name"],
            "Batch Number": b["batch_number"],
            "Stock Quantity": b["quantity_stocked"],
            "Expiry Date": b["expiry_date"],
            "Supplier": "Assigned"
        }
        if exp_date <= today_dt:
            row_exp["Severity"] = "🔴 Critical (Expired)"
            tier_critical.append(row_exp)
        elif today_dt < exp_date <= (today_dt + timedelta(days=30)):
            row_exp["Severity"] = "🟡 Medium (Expiring)"
            tier_medium.append(row_exp)
            
    # Render Tabs
    tab_crit, tab_high, tab_med = st.tabs([
        f"🔴 Critical ({len(tier_critical)})", 
        f"🟠 High Risk ({len(tier_high)})", 
        f"🟡 Medium Warning ({len(tier_medium)})"
    ])
    
    with tab_crit:
        if tier_critical:
            st.dataframe(pd.DataFrame(tier_critical), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Clear. Zero critical stocks or expired items found.")
            
    with tab_high:
        if tier_high:
            st.dataframe(pd.DataFrame(tier_high), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Clear. Zero high risk alerts found.")
            
    with tab_med:
        if tier_medium:
            st.dataframe(pd.DataFrame(tier_medium), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Clear. No medium warning batches found.")

# ==========================================
# PAGE 6: SUPPLIER REGISTRY
# ==========================================
elif page == texts["nav_p6"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p6']}</h3>", unsafe_allow_html=True)
    
    # Supplier table
    st.markdown("### 🤝 Supplier Contacts & Metrics Directory")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT supplier_name, contact_email, contact_phone, avg_lead_time_days, reliability_score
        FROM suppliers
        WHERE tenant_id = ?;
    """, (tenant_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        df_supps = pd.DataFrame([{
            "Supplier Name": r["supplier_name"],
            "Email Address": r["contact_email"],
            "Phone / Contact": r["contact_phone"],
            "Avg Lead Time (Days)": r["avg_lead_time_days"],
            "Reliability Rating (%)": f"{r['reliability_score']}%"
        } for r in rows])
        st.dataframe(df_supps, use_container_width=True, hide_index=True)
    else:
        st.info("No suppliers cataloged in this tenant. Add suppliers in CRUD page.")

# ==========================================
# PAGE 7: REPORTS & EXPORTS
# ==========================================
elif page == texts["nav_p7"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p7']}</h3>", unsafe_allow_html=True)
    
    st.markdown("### 📄 Relational Restocking Procurement Orders")
    
    if reorder_proc_suggestions:
        df_order = pd.DataFrame(reorder_proc_suggestions)
        
        # Renders table
        st.dataframe(df_order, use_container_width=True, hide_index=True)
        
        total_order_qty = df_order["Recommended Qty"].sum()
        total_est_cost = df_order["Estimated Cost (₹)"].sum()
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Total Procurement Order Units", f"{total_order_qty} units")
        with col_s2:
            st.metric("Total procurement Estimate Cost (₹)", f"₹{total_est_cost:,.2f}")
            
        # Download reports block
        st.markdown("### 📥 Download CSV Sheet")
        csv_rec = df_order.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=texts["btn_download_rec"],
            data=csv_rec,
            file_name="procurement_order_sheet.csv",
            mime="text/csv"
        )
        
        # Copy paste text report
        st.markdown("##### 📝 Procurement Report Printout")
        report_text = f"""=====================================================================
OFFICIAL CLINIC PROCUREMENT REPORT (AI AUTOGENERATED)
GENERATED ON: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
RURAL PHC CLINIC PORTAL - {user['tenant_name']}
=====================================================================
TOTAL ORDER ITEMS  : {total_order_qty} units
ESTIMATED COST      : INR {total_est_cost:,.2f}
ORDER BREAKDOWN:
"""
        for _, r in df_order.iterrows():
            report_text += f"- {r['Medicine Name']} ({r['Marathi Label']}) | Qty: {r['Recommended Qty']} units | Cost: ₹{r['Estimated Cost (₹)']} | Supplier: {r['Supplier Name']}\n"
        
        st.text_area("", report_text, height=200)
    else:
        st.success("✅ Excellent! Your branch unexpired shelf stock is completely safe. No procurement order needed.")

# ==========================================
# PAGE 8: SETUP & SIGN UP
# ==========================================
elif page == texts["nav_p8"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p8']}</h3>", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Multi-Tenant Clinic Management Controls")
    
    signup_tabs = st.tabs(["🔒 Register New Manager / Pharmacist", "🏢 Add New Branch Location", "🏢 Register New Healthcare Group (Tenant)"])
    
    # 1. Register User Signup
    with signup_tabs[0]:
        st.markdown("#### Create Secure Portal Account")
        with st.form("signup_user_form", clear_on_submit=True):
            s_user = st.text_input("Username*", placeholder="e.g. pharmacistsunil")
            s_pwd = st.text_input("Password*", type="password", placeholder="••••••••")
            s_name = st.text_input("Full Name*", placeholder="e.g. Sunil Deshmukh")
            s_role = st.selectbox("Role Clearance Level*", ["Pharmacist", "Manager", "Admin"])
            
            # Fetch branches to assign
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT branch_id, branch_name FROM branches WHERE tenant_id = ?;", (tenant_id,))
            branches_list = cursor.fetchall()
            conn.close()
            
            branch_dict = {row["branch_name"]: row["branch_id"] for row in branches_list}
            s_branch = st.selectbox("Assign Branch Location*", list(branch_dict.keys()))
            
            submitted_signup = st.form_submit_button("REGISTER OPERATOR")
            if submitted_signup:
                if not s_user or not s_pwd or not s_name:
                    st.error("Please fill in all starred inputs.")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        hp = hash_password(s_pwd)
                        b_id = branch_dict.get(s_branch)
                        cursor.execute("""
                            INSERT INTO users (tenant_id, branch_id, username, password_hash, role, full_name)
                            VALUES (?, ?, ?, ?, ?, ?);
                        """, (tenant_id, b_id, s_user, hp, s_role, s_name))
                        conn.commit()
                        st.success(f"Successfully registered **{s_name}** as **{s_role}**!")
                    except sqlite3.IntegrityError:
                        st.error("Username already taken. Please choose another username.")
                    finally:
                        conn.close()
                        
    # 2. Add Branch Location
    with signup_tabs[1]:
        st.markdown("#### Register New Clinic Location")
        with st.form("add_branch_form", clear_on_submit=True):
            b_name = st.text_input("Branch Clinic Name*", placeholder="e.g. PHC Indapur Clinic")
            b_loc = st.text_input("Location / Address", placeholder="e.g. Pune East, MH")
            
            submitted_branch = st.form_submit_button("ADD BRANCH")
            if submitted_branch:
                if not b_name:
                    st.error("Please specify a branch name.")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO branches (tenant_id, branch_name, location)
                        VALUES (?, ?, ?);
                    """, (tenant_id, b_name, b_loc))
                    conn.commit()
                    conn.close()
                    st.success(f"Successfully registered new branch location: **{b_name}**!")
                    
    # 3. Add Healthcare Group (Tenant)
    with signup_tabs[2]:
        st.markdown("#### Register New Group Tenant")
        with st.form("add_tenant_form", clear_on_submit=True):
            t_company = st.text_input("Company / Healthcare Group Name*", placeholder="e.g. Sahara Rural Healthcare")
            t_admin_user = st.text_input("Super-Admin Username*", placeholder="e.g. sahara_admin")
            t_admin_pwd = st.text_input("Super-Admin Password*", type="password", placeholder="••••••••")
            t_admin_name = st.text_input("Super-Admin Full Name*", placeholder="e.g. Dr. Patil")
            
            submitted_tenant = st.form_submit_button("REGISTER TENANT SYSTEM")
            if submitted_tenant:
                if not t_company or not t_admin_user or not t_admin_pwd or not t_admin_name:
                    st.error("Please specify all starred fields.")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO tenants (company_name) VALUES (?);", (t_company,))
                        new_t_id = cursor.lastrowid
                        
                        # Add a default corporate branch
                        cursor.execute("INSERT INTO branches (tenant_id, branch_name, location) VALUES (?, 'Corporate HQ', 'All Locations');", (new_t_id,))
                        new_b_id = cursor.lastrowid
                        
                        # Add super-admin
                        cursor.execute("""
                            INSERT INTO users (tenant_id, branch_id, username, password_hash, role, full_name)
                            VALUES (?, ?, ?, ?, 'Admin', ?);
                        """, (new_t_id, new_b_id, t_company, hash_password(t_admin_pwd), t_admin_name))
                        conn.commit()
                        st.success(f"Tenant **{t_company}** registered successfully! Log out and use the super-admin account to configure.")
                    except sqlite3.IntegrityError:
                        st.error("Healthcare Group or Admin Username already registered.")
                    finally:
                        conn.close()
