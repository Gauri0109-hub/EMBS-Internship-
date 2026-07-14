# =====================================================================
# MODULE: Utilities and Visualizations (utils.py)
# DESCRIPTION: Houses database querying wrappers and Plotly visualization builders.
# =====================================================================

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database.db_manager import get_connection

def fetch_medicine_list(tenant_id):
    """Fetches dictionary mapping medicine names to IDs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT medicine_id, medicine_name FROM medicines WHERE tenant_id = ?;", (tenant_id,))
    choices_med = {row["medicine_name"]: row["medicine_id"] for row in cursor.fetchall()}
    conn.close()
    return choices_med

def fetch_unexpired_usable_stock(medicine_id, branch_id):
    """Fetches total unexpired usable stock for a medicine from database inventory batches."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(quantity_stocked), 0) 
        FROM inventory 
        WHERE medicine_id = ? AND branch_id = ? AND expiry_date > DATE('now');
    """, (medicine_id, branch_id))
    usable_stock = cursor.fetchone()[0]
    conn.close()
    return usable_stock

def fetch_medicine_min_stock(medicine_id):
    """Fetches the safety threshold (ROP) for a medicine."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT min_required_stock FROM medicines WHERE medicine_id = ?;", (medicine_id,))
    row = cursor.fetchone()
    min_stock = row[0] if row and row[0] is not None else 20
    conn.close()
    return min_stock

def get_sales_timeline_db(medicine_id, branch_id):
    """Queries sales logs from sales_history table and returns continuous timeline."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sale_date, SUM(quantity_sold) as quantity_sold 
        FROM sales_history
        WHERE medicine_id = ? AND branch_id = ?
        GROUP BY sale_date
        ORDER BY sale_date ASC;
    """, (medicine_id, branch_id))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return pd.DataFrame()
        
    df = pd.DataFrame([{
        "date": pd.to_datetime(row["sale_date"]),
        "quantity_sold": row["quantity_sold"]
    } for row in rows])
    
    df.set_index("date", inplace=True)
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
    df = df.reindex(full_range, fill_value=0).reset_index().rename(columns={"index": "date"})
    
    return df

# Plotly visualization helpers
def build_stock_vs_demand_chart(df_results):
    """
    Creates a Plotly Bar Chart comparing Current Stock vs Predicted Demand.
    df_results should have columns: 'Medicine Name', 'Current Stock', 'Predicted Demand'
    """
    fig = px.bar(
        df_results,
        x="Medicine Name",
        y=["Current Stock", "Predicted Demand"],
        barmode="group",
        labels={"value": "Quantity (Units)", "variable": "Stock Type"},
        color_discrete_sequence=["#008080", "#ff9800"],
        title="Current Stock vs Predicted Demand"
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.5)")
    )
    return fig

def build_demand_forecast_chart(med_name, timeline_df, forecast_df):
    """
    Creates a Line Chart displaying past usage and forecasted future demand.
    """
    fig = go.Figure()
    
    # Slice past timeline to last 45 days for readability
    hist_tail = timeline_df.tail(45)
    
    fig.add_trace(go.Scatter(
        x=hist_tail["date"],
        y=hist_tail["quantity_sold"],
        mode="lines+markers",
        name="Past Usage (Units)",
        line=dict(color="#1f77b4", width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["predicted_usage"],
        mode="lines+markers",
        name="Forecast Demand (Units)",
        line=dict(color="#ff7f0e", width=2, dash="dash")
    ))
    
    fig.update_layout(
        title=f"Medicine Demand Forecast & History: {med_name}",
        xaxis_title="Date",
        yaxis_title="Units Dispensed Daily",
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.5)"),
        hovermode="x unified",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def build_risk_distribution_chart(df_results):
    """
    Creates a Pie Chart showing distribution of medicine risk levels.
    """
    # Count of each risk level
    risk_counts = df_results["Risk Level"].value_counts().reset_index()
    risk_counts.columns = ["Risk Level", "Count"]
    
    color_map = {
        "Critical": "#c62828",       # Red
        "High Risk": "#f57c00",      # Orange
        "Medium Warning": "#fbc02d", # Yellow
        "Safe": "#2e7d32"            # Green
    }
    
    fig = px.pie(
        risk_counts,
        values="Count",
        names="Risk Level",
        color="Risk Level",
        color_discrete_map=color_map,
        title="Inventory Risk Classification Distribution",
        hole=0.4
    )
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig
