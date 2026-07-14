# =====================================================================
# PROJECT: Industry-Ready Pharmacy AI Platform
# MODULE: Security & Authentication Services (auth_service.py)
# DESCRIPTION: Manages user login states, hashes password hashes, validates credentials,
#             and verifies role levels for RBAC (Role-Based Access Control).
#
# EXPLAINER FOR BEGINNERS:
# - Session State: A mechanism in Streamlit that remembers variables across clicks
#   and refreshes. We use it to save details of the logged-in user.
# - RBAC: Restricting what a user can see depending on their job title
#   (Admin, Manager, Pharmacist).
# =====================================================================

import streamlit as st
from database.db_manager import get_connection, hash_password

def authenticate_user(username, password):
    """
    Validates user credentials against the SQLite database.
    - If valid: Returns a dictionary of user properties (id, role, branch, tenant).
    - If invalid: Returns None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed_pwd = hash_password(password)
    
    # Query user details alongside tenant & branch information
    cursor.execute("""
        SELECT u.user_id, u.username, u.role, u.full_name, u.tenant_id, u.branch_id, 
               t.company_name, b.branch_name
        FROM users u
        JOIN tenants t ON u.tenant_id = t.tenant_id
        LEFT JOIN branches b ON u.branch_id = b.branch_id
        WHERE u.username = ? AND u.password_hash = ?;
    """, (username, hashed_pwd))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "role": row["role"],
            "full_name": row["full_name"],
            "tenant_id": row["tenant_id"],
            "branch_id": row["branch_id"],
            "tenant_name": row["company_name"],
            "branch_name": row["branch_name"] if row["branch_name"] else "All Branches"
        }
    return None

def verify_role_access(required_roles):
    """
    Halts Streamlit execution or returns false if the currently logged in user
    does not hold the required clearance level.
    """
    if "user" not in st.session_state:
        return False
    
    user_role = st.session_state.user["role"]
    if user_role in required_roles:
        return True
    return False

def show_login_interface():
    """Renders a gorgeous modern medical-themed login panel."""
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
                    user_session = authenticate_user(username_input, password_input)
                    if user_session:
                        st.session_state.user = user_session
                        st.success(f"Welcome back, **{user_session['full_name']}**! Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please try again.")
                        
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
