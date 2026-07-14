# =====================================================================
# PROJECT: Enterprise Pharmacy AI Platform
# MODULE: Upgraded Main Application Wrapper (app.py)
# DESCRIPTION: Streamlit frontend web app rendering the 8 production pages:
#             Dashboard, Inventory CRUD, spreadsheet Data Uploads, Predictions,
#             Alerts watch, Supplier registry, Reports center, and secure Sign Up.
#             Uses REST APIs to connect to the FastAPI backend server.
# =====================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import requests

# Base API configuration
API_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1")

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

# Helper functions for API calls
def get_headers():
    headers = {}
    if "token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return headers

def api_get(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}", headers=get_headers())
        if response.status_code == 401:
            st.warning("Session expired. Please log in again.")
            if "user" in st.session_state:
                del st.session_state["user"]
            if "token" in st.session_state:
                del st.session_state["token"]
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Backend connection error: {e}")
        return None

def api_post(endpoint, data=None, json=None, files=None):
    try:
        response = requests.post(f"{API_URL}{endpoint}", data=data, json=json, files=files, headers=get_headers())
        if response.status_code == 401:
            st.warning("Session expired. Please log in again.")
            if "user" in st.session_state:
                del st.session_state["user"]
            if "token" in st.session_state:
                del st.session_state["token"]
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Backend connection error: {e}")
        return None

def api_put(endpoint, json=None):
    try:
        response = requests.put(f"{API_URL}{endpoint}", json=json, headers=get_headers())
        if response.status_code == 401:
            st.warning("Session expired. Please log in again.")
            if "user" in st.session_state:
                del st.session_state["user"]
            if "token" in st.session_state:
                del st.session_state["token"]
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Backend connection error: {e}")
        return None

def api_delete(endpoint):
    try:
        response = requests.delete(f"{API_URL}{endpoint}", headers=get_headers())
        if response.status_code == 401:
            st.warning("Session expired. Please log in again.")
            if "user" in st.session_state:
                del st.session_state["user"]
            if "token" in st.session_state:
                del st.session_state["token"]
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Backend connection error: {e}")
        return None

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
        "clinic_badge": "📍 Enterprise Clinic Portal | Synced with FastAPI & PostgreSQL.",
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
        "clinic_badge": "📍 बहु-भाडेकरू क्लिनिक पोर्टल | FastAPI आणि PostgreSQL कनेक्ट.",
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
    
    st.markdown("""
        <div style='background-color:#e0f2f1; padding:15px; border-radius:8px; text-align:center; border: 1px solid #b2dfdb; margin-bottom: 20px;'>
            <h4 style='color:#004d40; margin:0;'>🔐 SECURE CLINICAL ACCESS PORTAL</h4>
            <p style='color:#00796b; margin:3px 0 0 0; font-size:0.85rem;'>Please log in to query medicine predictions, audit stocks, and configure supply chain logs.</p>
        </div>
    """, unsafe_allow_html=True)
    
    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    with login_col2:
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username / वापरकर्ता नाव", placeholder="e.g. pharmacist")
            password_input = st.text_input("Password / पासवर्ड", type="password", placeholder="••••••••")
            
            btn_login = st.form_submit_button("LOGIN / लॉगिन करा")
            
            if btn_login:
                if not username_input or not password_input:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Authenticating..."):
                        try:
                            response = requests.post(
                                f"{API_URL}/auth/login", 
                                data={"username": username_input, "password": password_input}
                            )
                            if response.status_code == 200:
                                tokens = response.json()
                                st.session_state.token = tokens["access_token"]
                                st.session_state.refresh_token = tokens["refresh_token"]
                                
                                # Query user info
                                me_resp = requests.get(
                                    f"{API_URL}/auth/me", 
                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                )
                                if me_resp.status_code == 200:
                                    st.session_state.user = me_resp.json()
                                    st.success(f"Welcome back! Redirecting...")
                                    st.rerun()
                                else:
                                    st.error("Failed to fetch user profile details.")
                            else:
                                st.error("Invalid username or password. Please try again.")
                        except Exception as e:
                            st.error(f"Cannot connect to the backend server: {e}")
                            
        # Display demo login instructions
        st.markdown("""
            <div style='background-color:#fafafa; border-radius:6px; padding:10px; font-size:0.8rem; border:1px solid #eee; margin-top: 15px;'>
                <p style='margin:0 0 5px 0; font-weight:600; color:#555;'>🔑 Demo Credentials for Testing:</p>
                <ul style='margin:0; padding-left:20px; color:#666;'>
                    <li><b>Admin:</b> admin / admin123 (Manage tenants & all branches)</li>
                    <li><b>Manager:</b> manager / manager123 (Add stocks & suppliers)</li>
                    <li><b>Pharmacist:</b> pharmacist / pharma123 (Record daily sales)</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
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
    if "token" in st.session_state:
        del st.session_state["token"]
    st.cache_data.clear()
    st.rerun()
    
st.sidebar.markdown("---")

# Bilingual switch
lang_toggle = st.sidebar.checkbox("मराठीत पहा / View in Marathi", value=False)
lang = "Marathi" if lang_toggle else "English"
texts = TRANSLATIONS[lang]

# Responsive Theme Control
dark_mode = st.sidebar.checkbox("🌓 Toggle Dark Mode", value=False)
if dark_mode:
    st.markdown("""
        <style>
        .stApp {
            background-color: #121212;
            color: #e0e0e0;
        }
        .main-title {
            color: #80cbc4 !important;
        }
        .sub-title {
            color: #26a69a !important;
        }
        .page-header {
            color: #80cbc4 !important;
            border-bottom-color: #004d40 !important;
        }
        .metric-card {
            background-color: #1e1e1e !important;
            color: #e0e0e0 !important;
        }
        .metric-green {
            background-color: #1b5e20 !important;
            border-left-color: #4caf50 !important;
            color: #e8f5e9 !important;
        }
        .metric-yellow {
            background-color: #f57f17 !important;
            border-left-color: #fbc02d !important;
            color: #fffde7 !important;
        }
        .metric-red {
            background-color: #b71c1c !important;
            border-left-color: #f44336 !important;
            color: #ffebee !important;
        }
        .metric-blue {
            background-color: #006064 !important;
            border-left-color: #00bcd4 !important;
            color: #e0f2f1 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# 9 Page Sidebar Radio Selector
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
        texts["nav_p8"],
        "🤖 AI Assistant Chat"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"<div class='clinic-banner'>{texts['clinic_badge']}</div>", unsafe_allow_html=True)

# Main Title Headers
st.markdown(f"<div class='main-title'>{texts['title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>{texts['subtitle']}</div>", unsafe_allow_html=True)

# Fetch dynamic warning metrics from backend REST APIs
rop_resp = api_get("/reports/suggestions")
reorder_proc_suggestions = rop_resp.json() if rop_resp and rop_resp.status_code == 200 else []

count_red = sum(1 for r in reorder_proc_suggestions if "OUT OF STOCK" in r["Status"])
count_yellow = sum(1 for r in reorder_proc_suggestions if "Low Stock" in r["Status"])

meds_resp = api_get("/medicines")
medicines_catalog = meds_resp.json() if meds_resp and meds_resp.status_code == 200 else []
tot_meds = len(medicines_catalog)
tot_crit = sum(1 for m in medicines_catalog if m["is_critical"])

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
    
    inv_resp = api_get("/inventory")
    inventory_items = inv_resp.json() if inv_resp and inv_resp.status_code == 200 else []
    
    if medicines_catalog:
        # Aggregate inventory stock in python
        stock_map = {}
        for item in inventory_items:
            # Exclude expired
            exp_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
            if exp_date > datetime.now().date():
                m_id = item["medicine_id"]
                stock_map[m_id] = stock_map.get(m_id, 0) + item["quantity_stocked"]
                
        df_stock_list = []
        for m in medicines_catalog:
            df_stock_list.append({
                "Medicine": m["medicine_name"],
                "Usable Stock": stock_map.get(m["medicine_id"], 0),
                "Safety Threshold": m["min_required_stock"]
            })
            
        df_stock = pd.DataFrame(df_stock_list)
        
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
    
    inv_resp = api_get("/inventory")
    inventory_items = inv_resp.json() if inv_resp and inv_resp.status_code == 200 else []
    
    supp_resp = api_get("/suppliers")
    suppliers_catalog = supp_resp.json() if supp_resp and supp_resp.status_code == 200 else []
    
    if medicines_catalog:
        stock_map_total = {}
        stock_map_usable = {}
        for item in inventory_items:
            m_id = item["medicine_id"]
            stock_map_total[m_id] = stock_map_total.get(m_id, 0) + item["quantity_stocked"]
            exp_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
            if exp_date > datetime.now().date():
                stock_map_usable[m_id] = stock_map_usable.get(m_id, 0) + item["quantity_stocked"]
                
        supp_name_map = {s["supplier_id"]: s["supplier_name"] for s in suppliers_catalog}
        
        df_meds = pd.DataFrame([{
            "ID": f"MED{m['medicine_id']:03d}",
            "Medicine Name": m["medicine_name"],
            "Bilingual Label": m["bilingual_name"] if m["bilingual_name"] else "N/A",
            "Total Shelf Stock": stock_map_total.get(m["medicine_id"], 0),
            "Usable Stock (Unexpired)": stock_map_usable.get(m["medicine_id"], 0),
            "Min Safety Level": m["min_required_stock"],
            "Unit Price (₹)": m["unit_price"],
            "Preferred Supplier": supp_name_map.get(m["preferred_supplier_id"], "Unassigned"),
            "Is Critical?": "Yes 🚨" if m["is_critical"] else "No",
            "id_raw": m["medicine_id"]
        } for m in medicines_catalog])
        
        # Search parameters
        s_col1, s_col2 = st.columns([2, 1])
        with s_col1:
            q_term = st.text_input("🔍 Search Medicine Inventory", "")
        with s_col2:
            sel_category = st.selectbox("📁 Filter Options", ["All", "Critical Only", "Normal Only"])
            
        df_filtered_meds = df_meds.copy()
        if q_term:
            df_filtered_meds = df_filtered_meds[df_filtered_meds["Medicine Name"].str.contains(q_term, case=False)]
        if sel_category == "Critical Only":
            df_filtered_meds = df_filtered_meds[df_filtered_meds["Is Critical?"] == "Yes 🚨"]
        elif sel_category == "Normal Only":
            df_filtered_meds = df_filtered_meds[df_filtered_meds["Is Critical?"] == "No"]
            
        st.dataframe(df_filtered_meds.drop(columns=["id_raw"]), use_container_width=True, hide_index=True)
    else:
        df_filtered_meds = pd.DataFrame()
        st.warning("No medicines active in this tenant branch database.")
        
    has_modify_access = user["role"] in ["Administrator", "Branch Manager"]
    
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
                a_price = st.number_input("Unit Price (₹)", min_value=0.1, value=5.0)
                a_min = st.number_input("Minimum Stock Threshold Level", min_value=5, value=20)
                a_crit = st.selectbox("Is this medicine life-saving / critical?", ["No", "Yes"])
                
                supp_dict = {s["supplier_name"]: s["supplier_id"] for s in suppliers_catalog}
                a_supp = st.selectbox("Preferred Supplier Link", ["None"] + list(supp_dict.keys()))
                
                submitted_add = st.form_submit_button("ADD FORMULATION")
                if submitted_add:
                    if not a_name or not a_mr:
                        st.error("Please fill in all starred inputs.")
                    else:
                        pref_id = supp_dict.get(a_supp)
                        res = api_post("/medicines", json={
                            "medicine_name": a_name,
                            "bilingual_name": a_mr,
                            "unit_price": a_price,
                            "is_critical": True if a_crit == "Yes" else False,
                            "preferred_supplier_id": pref_id,
                            "min_required_stock": a_min,
                            "tenant_id": tenant_id
                        })
                        if res and res.status_code == 200:
                            st.success(f"Added **{a_name}** successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add medicine. It may already exist.")
                            
        # 2. Edit Medicine
        with crud_tabs[1]:
            if not df_filtered_meds.empty:
                st.markdown("#### Modify Medicine Properties")
                with st.form("edit_med_form"):
                    select_edit_med = st.selectbox("Select Medicine to Edit", df_filtered_meds["Medicine Name"].unique())
                    row_edit = df_filtered_meds[df_filtered_meds["Medicine Name"] == select_edit_med].iloc[0]
                    
                    e_name = st.text_input("Medicine Name (English)", value=row_edit["Medicine Name"])
                    e_mr = st.text_input("Bilingual Label (Marathi)", value=row_edit["Bilingual Label"])
                    e_price = st.number_input("Unit Price (₹)", min_value=0.1, value=float(row_edit["Unit Price (₹)"]))
                    e_min = st.number_input("Minimum Stock Level Limit", min_value=5, value=int(row_edit["Min Safety Level"]))
                    e_crit = st.selectbox("Is Critical?", ["No", "Yes"], index=1 if "Yes" in row_edit["Is Critical?"] else 0)
                    
                    supp_dict = {s["supplier_name"]: s["supplier_id"] for s in suppliers_catalog}
                    default_supp_name = row_edit["Preferred Supplier"]
                    e_supp = st.selectbox(
                        "Preferred Supplier", 
                        ["None"] + list(supp_dict.keys()), 
                        index=list(supp_dict.keys()).index(default_supp_name)+1 if default_supp_name in supp_dict else 0
                    )
                    
                    submitted_edit = st.form_submit_button("SAVE MODIFIED PROPERTIES")
                    if submitted_edit:
                        pref_id = supp_dict.get(e_supp)
                        res = api_put(f"/medicines/{int(row_edit['id_raw'])}", json={
                            "medicine_name": e_name,
                            "bilingual_name": e_mr,
                            "unit_price": e_price,
                            "is_critical": True if e_crit == "Yes" else False,
                            "preferred_supplier_id": pref_id,
                            "min_required_stock": e_min
                        })
                        if res and res.status_code == 200:
                            st.success("Successfully modified properties!")
                            st.rerun()
                        else:
                            st.error("Failed to modify medicine properties.")
            else:
                st.write("No medicine catalog records to edit.")
                
        # 3. Delete Medicine
        with crud_tabs[2]:
            if not df_filtered_meds.empty:
                st.markdown("#### Remove Formulation from Database")
                select_del_med = st.selectbox("Choose Medicine to Delete", df_filtered_meds["Medicine Name"].unique())
                row_del = df_filtered_meds[df_filtered_meds["Medicine Name"] == select_del_med].iloc[0]
                del_confirm = st.checkbox("Confirm permanent deletion of formulation and all its batch inventory")
                btn_delete_exe = st.button("DELETE FORMULATION")
                
                if btn_delete_exe:
                    if not del_confirm:
                        st.error("Please check the confirmation box.")
                    else:
                        res = api_delete(f"/medicines/{int(row_del['id_raw'])}")
                        if res and res.status_code == 204:
                            st.success(f"Permanently deleted **{select_del_med}** from database.")
                            st.rerun()
                        else:
                            st.error("Failed to delete medicine formulation.")
            else:
                st.write("No medicine catalog records to delete.")
                
        # 4. Record Incoming Batch
        with crud_tabs[3]:
            if not df_filtered_meds.empty:
                st.markdown("#### Log Incoming Supply Shipment Batch")
                with st.form("incoming_batch_form", clear_on_submit=True):
                    sel_batch_med = st.selectbox("Select Medicine Received", df_filtered_meds["Medicine Name"].unique())
                    med_id_raw = df_filtered_meds[df_filtered_meds["Medicine Name"] == sel_batch_med]["id_raw"].values[0]
                    
                    b_qty = st.number_input("Quantity Received (Units)", min_value=1, value=100)
                    b_exp = st.date_input("Expiry Date", min_value=datetime.today())
                    
                    submitted_batch = st.form_submit_button("LOG BATCH")
                    if submitted_batch:
                        res = api_post("/inventory", json={
                            "medicine_id": int(med_id_raw),
                            "batch_number": f"BAT-{datetime.now().strftime('%m%d%H%M')}",
                            "quantity_stocked": int(b_qty),
                            "expiry_date": b_exp.strftime("%Y-%m-%d")
                        })
                        if res and res.status_code == 200:
                            st.success("Log incoming supply batch successful!")
                            st.rerun()
                        else:
                            st.error("Failed to log batch to inventory.")
            else:
                st.write("No medicine catalog records to log batches.")
    else:
        st.info("ℹ️ Managers and Admins hold full clearance to edit catalog records and log incoming batches. Your clearance is restricted to read-only.")

# ==========================================
# PAGE 3: DATA INGEST UPLOAD
# ==========================================
elif page == texts["nav_p3"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p3']}</h3>", unsafe_allow_html=True)
    
    has_modify_access = user["role"] in ["Administrator", "Branch Manager"]
    if not has_modify_access:
        st.warning("⚠️ Access Denied: Bulk spreadsheet importing requires Manager or Admin clearance level.")
    else:
        st.markdown("Upload your Excel (`.xlsx`) or CSV files here. The schema cleanses dates and validates columns automatically.")
        
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
            
            with st.spinner("Processing Ingestion Pipeline on Backend..."):
                file_bytes = uploaded_file.read()
                files = {"file": (filename, file_bytes, "application/octet-stream")}
                
                if "Inventory" in upload_type:
                    res = api_post("/inventory/import", files=files)
                else:
                    res = api_post("/forecast/import", files=files)
                    
                if res and res.status_code == 201:
                    st.success(f"🏆 {res.json()['message']}")
                    st.cache_data.clear()
                    st.rerun()
                elif res:
                    st.error(f"🔴 Import failed: {res.json().get('detail', 'Unknown error')}")

# ==========================================
# PAGE 4: ML PREDICTIONS
# ==========================================
elif page == texts["nav_p4"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p4']}</h3>", unsafe_allow_html=True)
    
    st.markdown("#### 🛠️ Forecast Configuration")
    f_horizon = st.selectbox("Select Forecast Horizon", ["Next 7 Days", "Next 14 Days", "Next 30 Days"], index=2)
    horizon_days = 7 if "7" in f_horizon else (14 if "14" in f_horizon else 30)
    
    if medicines_catalog:
        results_rows = []
        detailed_ml_results = {}
        
        # We loop and hit /forecast/{med_id} for all medicines
        with st.spinner("Querying ML forecasting statistics on backend..."):
            for m in medicines_catalog:
                med_id = m["medicine_id"]
                med_name = m["medicine_name"]
                
                # Fetch forecast
                fc_resp = api_get(f"/forecast/{med_id}?days_to_forecast={horizon_days}")
                if fc_resp and fc_resp.status_code == 200:
                    data = fc_resp.json()
                    
                    # Usable Stock (Frontend local state matching)
                    usable_stock = 0
                    for item in inventory_items:
                        if item["medicine_id"] == med_id:
                            exp_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
                            if exp_date > datetime.now().date():
                                usable_stock += item["quantity_stocked"]
                                
                    # Sum predicted demand over forecast horizon
                    pred_demand = sum(f["predicted_usage"] for f in data["forecast"])
                    diff = pred_demand - usable_stock
                    
                    # Risk status from backend logic approximation or simulate here
                    days_left = 999
                    temp_stock = usable_stock
                    for idx, f in enumerate(data["forecast"]):
                        temp_stock -= f["predicted_usage"]
                        if temp_stock <= 0:
                            days_left = idx + 1
                            break
                            
                    if days_left <= 7:
                        risk_level = "Critical"
                        recommended_action = "Restock immediately!"
                    elif days_left <= 14:
                        risk_level = "High Risk"
                        recommended_action = "Place order within 48 hours."
                    elif days_left <= 30 or usable_stock < m["min_required_stock"]:
                        risk_level = "Medium Warning"
                        recommended_action = "Monitor stock and plan order."
                    else:
                        risk_level = "Safe"
                        recommended_action = "No action required."
                        
                    results_rows.append({
                        "Medicine Name": med_name,
                        "Current Stock": usable_stock,
                        "Predicted Demand": pred_demand,
                        "Difference": diff,
                        "Risk Level": risk_level,
                        "Recommended Action": recommended_action,
                        "medicine_id": med_id
                    })
                    
                    detailed_ml_results[med_id] = {
                        "best_model_name": data["best_model_name"],
                        "metrics": f"MAE: {data['metrics']['MAE']} | RMSE: {data['metrics']['RMSE']} | MAPE: {data['metrics']['MAPE']}% | Accuracy: {data['metrics']['Accuracy']}%",
                        "xai": data["feature_importance"],
                        "shap": data["shap_values"],
                        "forecast": data["forecast"],
                        "history": data["history"],
                        "days_left": days_left,
                        "stockout_date": data["forecast"][days_left-1]["date"] if days_left <= len(data["forecast"]) else "Safe (>30 Days)"
                    }
                    
        if results_rows:
            df_results = pd.DataFrame(results_rows)
            
            # Display summary table
            st.markdown("### 📊 Pharmacy Predictions Dashboard Output")
            df_display = df_results.copy()
            df_display["Difference (Units)"] = df_display["Difference"].apply(lambda x: f"+{x} Shortage" if x > 0 else f"{abs(x)} Surplus")
            st.dataframe(
                df_display[["Medicine Name", "Current Stock", "Predicted Demand", "Difference (Units)", "Risk Level", "Recommended Action"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Draw charts
            st.markdown("---")
            st.markdown("### 📈 Prediction Visualizations")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                # Risk Pie Chart
                risk_counts = df_results["Risk Level"].value_counts().reset_index()
                risk_counts.columns = ["Risk Level", "Count"]
                color_map = {"Critical": "#c62828", "High Risk": "#f57c00", "Medium Warning": "#fbc02d", "Safe": "#2e7d32"}
                fig_risk = px.pie(risk_counts, values="Count", names="Risk Level", color="Risk Level", color_discrete_map=color_map, title="Risk Distribution", hole=0.4)
                st.plotly_chart(fig_risk, use_container_width=True)
            with col_c2:
                # Bar Chart
                fig_bar = px.bar(df_results, x="Medicine Name", y=["Current Stock", "Predicted Demand"], barmode="group", title="Current Stock vs Predicted Demand", color_discrete_sequence=["#008080", "#ff9800"])
                st.plotly_chart(fig_bar, use_container_width=True)
                
            # Drill-down
            st.markdown("---")
            st.markdown("### 🔍 Single Medicine Detail Drill-down")
            choices_med = {m["medicine_name"]: m["medicine_id"] for m in medicines_catalog}
            sel_med_name = st.selectbox("Choose Medicine to Drill-down", list(choices_med.keys()))
            sel_med_id = choices_med[sel_med_name]
            
            if sel_med_id in detailed_ml_results:
                res_detail = detailed_ml_results[sel_med_id]
                
                st.markdown(f"""
                    <div style='background-color:#e0f2f1; border-left: 5px solid #008080; border-radius: 8px; padding: 12px; font-size: 0.9rem; color: #004d40;'>
                        <p style='margin:0;'>🥇 <b>Best Model Selected:</b> {res_detail['best_model_name']}</p>
                        <p style='margin:4px 0 0 0; font-size:0.8rem; font-family: monospace;'><b>Metrics:</b> {res_detail['metrics']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    st.metric("Estimated Depletion Date", res_detail["stockout_date"])
                with col_k2:
                    st.metric("Days of Stock Left", f"{res_detail['days_left']} Days" if res_detail['days_left'] < 900 else "> 30 Days")
                    
                # Forecast vs Past plot
                hist_dates = [h["date"] for h in res_detail["history"]]
                hist_vals = [h["quantity_sold"] for h in res_detail["history"]]
                fc_dates = [f["date"] for f in res_detail["forecast"]]
                fc_vals = [f["predicted_usage"] for f in res_detail["forecast"]]
                
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(x=hist_dates, y=hist_vals, mode="lines+markers", name="Past Usage", line=dict(color="#1f77b4")))
                fig_timeline.add_trace(go.Scatter(x=fc_dates, y=fc_vals, mode="lines+markers", name="Forecast Demand", line=dict(color="#ff7f0e", dash="dash")))
                fig_timeline.update_layout(title="Demand Timeline Forecast", xaxis_title="Date", yaxis_title="Units daily", height=380)
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # Feature importance & SHAP side-by-side
                st.markdown("#### 🔮 Explainable AI (XAI) Drivers")
                col_x1, col_x2 = st.columns(2)
                with col_x1:
                    df_imp = pd.DataFrame([{"Feature": k.replace('_', ' ').title(), "Importance (%)": v} for k, v in res_detail["xai"].items()])
                    fig_imp = px.bar(df_imp.sort_values("Importance (%)"), x="Importance (%)", y="Feature", orientation="h", title="Global Feature Importance", color_discrete_sequence=["#008080"])
                    st.plotly_chart(fig_imp, use_container_width=True)
                with col_x2:
                    df_shap = pd.DataFrame([{"Feature": k.replace('_', ' ').title(), "SHAP Value": v} for k, v in res_detail["shap"].items()])
                    fig_shap = px.bar(df_shap.sort_values("SHAP Value"), x="SHAP Value", y="Feature", orientation="h", title="Local SHAP Explanation (XAI)", color_discrete_sequence=["#ff9800"])
                    st.plotly_chart(fig_shap, use_container_width=True)
    else:
        st.warning("No medicines active in this branch database.")

# ==========================================
# PAGE 5: ALERTS & RISKS
# ==========================================
elif page == texts["nav_p5"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p5']}</h3>", unsafe_allow_html=True)
    st.markdown("### 🚨 Relational Warnings & Safety Alarms")
    
    alert_resp = api_get("/alerts")
    alerts_list = alert_resp.json() if alert_resp and alert_resp.status_code == 200 else []
    
    tier_critical = []
    tier_high = []
    tier_medium = []
    
    for a in alerts_list:
        row_alert = {
            "ID": a["alert_id"],
            "Alert Type": a["alert_type"],
            "Message": a["message"],
            "Severity": a["severity"],
            "Resolved": "Yes" if a["is_resolved"] else "No"
        }
        if a["severity"] == "Critical":
            tier_critical.append(row_alert)
        elif a["severity"] == "High":
            tier_high.append(row_alert)
        else:
            tier_medium.append(row_alert)
            
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
            st.success("✅ Clear. No warning level alerts found.")
            
    # Resolve alerts block
    if alerts_list:
        st.markdown("---")
        st.markdown("#### 🔄 Resolve Alerts")
        unresolved_ids = [a["alert_id"] for a in alerts_list if not a["is_resolved"]]
        if unresolved_ids:
            sel_resolve_id = st.selectbox("Select Alert ID to Resolve", unresolved_ids)
            if st.button("Mark Alert as Resolved"):
                res = api_put(f"/alerts/{sel_resolve_id}/resolve")
                if res and res.status_code == 200:
                    st.success(f"Alert {sel_resolve_id} successfully marked as resolved!")
                    st.rerun()

# ==========================================
# PAGE 6: SUPPLIER REGISTRY
# ==========================================
elif page == texts["nav_p6"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p6']}</h3>", unsafe_allow_html=True)
    st.markdown("### 🤝 Supplier Contacts & Metrics Directory")
    
    if suppliers_catalog:
        df_supps = pd.DataFrame([{
            "Supplier Name": s["supplier_name"],
            "Email Address": s["contact_email"] if s["contact_email"] else "N/A",
            "Phone / Contact": s["contact_phone"] if s["contact_phone"] else "N/A",
            "Avg Lead Time (Days)": s["avg_lead_time_days"],
            "Reliability Rating (%)": f"{s['reliability_score']}%"
        } for s in suppliers_catalog])
        st.dataframe(df_supps, use_container_width=True, hide_index=True)
    else:
        st.info("No suppliers cataloged. Register supplier in forms.")
        
    has_modify_access = user["role"] in ["Administrator", "Branch Manager"]
    if has_modify_access:
        st.markdown("---")
        st.markdown("#### 🤝 Register New Supplier Contact")
        with st.form("supplier_reg_form", clear_on_submit=True):
            s_name = st.text_input("Supplier Name*", placeholder="e.g. Maurya Distributors")
            s_email = st.text_input("Contact Email", placeholder="e.g. order@mauryapharma.com")
            s_phone = st.text_input("Contact Phone", placeholder="e.g. +91 98234 56781")
            s_lead = st.number_input("Average Lead Time (Days)", min_value=1.0, value=5.0)
            s_rel = st.number_input("Supplier Reliability Rating (%)", min_value=10.0, max_value=100.0, value=100.0)
            
            submitted_supp = st.form_submit_button("REGISTER SUPPLIER")
            if submitted_supp:
                if not s_name:
                    st.error("Please enter a supplier name.")
                else:
                    res = api_post("/suppliers", json={
                        "supplier_name": s_name,
                        "contact_email": s_email if s_email else None,
                        "contact_phone": s_phone if s_phone else None,
                        "avg_lead_time_days": s_lead,
                        "reliability_score": s_rel,
                        "tenant_id": tenant_id
                    })
                    if res and res.status_code == 200:
                        st.success(f"Supplier **{s_name}** successfully registered!")
                        st.rerun()
                    else:
                        st.error("Failed to register supplier contact.")

# ==========================================
# PAGE 7: REPORTS & EXPORTS
# ==========================================
elif page == texts["nav_p7"]:
    st.markdown(f"<h3 class='page-header'>{texts['nav_p7']}</h3>", unsafe_allow_html=True)
    st.markdown("### 📄 Relational Restocking Procurement Orders")
    
    if reorder_proc_suggestions:
        df_order = pd.DataFrame(reorder_proc_suggestions)
        st.dataframe(df_order, use_container_width=True, hide_index=True)
        
        total_order_qty = df_order["Recommended Qty"].sum()
        total_est_cost = df_order["Estimated Cost (₹)"].sum()
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Total Procurement Order Units", f"{total_order_qty} units")
        with col_s2:
            st.metric("Total procurement Estimate Cost (₹)", f"₹{total_est_cost:,.2f}")
            
        st.markdown("### 📥 Download Report Files")
        rep_col1, rep_col2, rep_col3 = st.columns(3)
        with rep_col1:
            # PDF download
            pdf_resp = api_get("/reports/pdf")
            if pdf_resp and pdf_resp.status_code == 200:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_resp.content,
                    file_name=f"procurement_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
        with rep_col2:
            # Excel download
            xlsx_resp = api_get("/reports/excel")
            if xlsx_resp and xlsx_resp.status_code == 200:
                st.download_button(
                    label="📥 Download Excel Report",
                    data=xlsx_resp.content,
                    file_name="procurement_orders.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        with rep_col3:
            # CSV download
            csv_resp = api_get("/reports/csv")
            if csv_resp and csv_resp.status_code == 200:
                st.download_button(
                    label="📥 Download CSV Report",
                    data=csv_resp.content,
                    file_name="procurement_orders.csv",
                    mime="text/csv"
                )
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
            s_role = st.selectbox("Role Clearance Level*", ["Pharmacist", "Branch Manager", "Administrator", "Supplier", "Government Officer"])
            
            # Fetch branches under this tenant
            branch_resp = api_get("/auth/branches")
            branches_list = branch_resp.json() if branch_resp and branch_resp.status_code == 200 else []
            branch_dict = {b["branch_name"]: b["branch_id"] for b in branches_list}
            
            s_branch = st.selectbox("Assign Branch Location*", list(branch_dict.keys()))
            
            submitted_signup = st.form_submit_button("REGISTER OPERATOR")
            if submitted_signup:
                if not s_user or not s_pwd or not s_name:
                    st.error("Please fill in all starred inputs.")
                else:
                    b_id = branch_dict.get(s_branch)
                    res = api_post("/auth/user", json={
                        "username": s_user,
                        "password": s_pwd,
                        "full_name": s_name,
                        "role": s_role,
                        "tenant_id": tenant_id,
                        "branch_id": b_id
                    })
                    if res and res.status_code == 200:
                        st.success(f"Successfully registered **{s_name}** as **{s_role}**!")
                    else:
                        st.error(f"Failed to register operator: {res.json().get('detail', 'Unknown error')}")
                        
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
                    res = api_post("/auth/branch", json={
                        "branch_name": b_name,
                        "location": b_loc,
                        "tenant_id": tenant_id
                    })
                    if res and res.status_code == 200:
                        st.success(f"Successfully registered new branch location: **{b_name}**!")
                    else:
                        st.error("Failed to add branch location.")
                        
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
                    res = requests.post(f"{API_URL}/auth/signup", json={
                        "company_name": t_company,
                        "admin_username": t_admin_user,
                        "admin_password": t_admin_pwd,
                        "admin_full_name": t_admin_name
                    })
                    if res.status_code == 200:
                        st.success(f"Tenant **{t_company}** registered successfully! Log out and use the super-admin account to configure.")
                    else:
                        st.error(f"Failed to register tenant group: {res.json().get('detail', 'Unknown error')}")

# ==========================================
# CHATBOT ASSISTANT PAGE (Gemini)
# ==========================================
elif page == "🤖 AI Assistant Chat":
    st.markdown("### 🤖 Gemini AI Clinical Inventory Chatbot")
    st.markdown("Ask the clinical assistant questions regarding stock status, outbreak predictions, or generate restock emails.")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    user_query = st.chat_input("Ask a question about today's inventory...")
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        with st.spinner("Gemini is thinking..."):
            res = api_post("/chatbot", json={
                "message": user_query,
                "history": st.session_state.chat_history[:-1]
            })
            if res and res.status_code == 200:
                reply = res.json()["reply"]
                with st.chat_message("assistant"):
                    st.write(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
            else:
                st.error("Failed to get chatbot reply from backend service.")
