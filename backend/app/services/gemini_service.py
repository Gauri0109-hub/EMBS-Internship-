import os
import google.generativeai as genai
from sqlalchemy.orm import Session
from backend.app.config.settings import settings
from backend.app.repositories.repositories import inventory_repo, alert_repo, medicine_repo
from backend.app.services.procurement_service import calculate_reorder_points

def configure_gemini():
    """Initializes the Google Generative AI client using the config key."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        # Fall back to environment check directly
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

def get_gemini_reply(message: str, history: list, branch_id: int, tenant_id: int, db: Session) -> str:
    """
    Interfaces with Gemini Pro to answer clinical inventory queries.
    Injects database context dynamically.
    """
    has_api = configure_gemini()
    if not has_api:
        return (
            "⚠️ **Gemini AI Configuration Missing:** The chatbot assistant requires a valid "
            "`GEMINI_API_KEY` set in your `.env` file to interface with Google's large language models. "
            "Please configure the key and try again.\n\n"
            "*Placeholder response for demonstration purposes only.*"
        )
        
    try:
        # Query context from database to inject into system prompts
        # 1. Active ROP suggestions
        reorder_suggestions = calculate_reorder_points(branch_id, tenant_id, db)
        low_stock_summary = []
        for r in reorder_suggestions[:15]:
            low_stock_summary.append(
                f"- {r['Medicine Name']}: Usable Stock = {r['Usable Stock']} units, ROP = {r['Reorder Point (ROP)']} units, Recommended Reorder = {r['Recommended Qty']} units, Preferred Supplier = {r['Supplier Name']}."
            )
        
        # 2. Expiry warnings
        unresolved_alerts = alert_repo.get_unresolved_alerts(db, branch_id)
        alert_summary = []
        for a in unresolved_alerts[:10]:
            alert_summary.append(f"- Alert: {a.alert_type} on Medicine ID {a.medicine_id} ({a.severity} severity): {a.message}")
            
        system_context = (
            "You are the Intelligent Clinical Inventory Assistant for a rural health clinic/small pharmacy in India. "
            "You help pharmacists manage their medicines, predict stockouts, and format restocking requests. "
            "Answer user questions accurately and professionally based on the real-time clinic database context provided below.\n\n"
            "=== CLINIC INVENTORY CONTEXT ===\n"
            f"Active Branch ID: {branch_id}\n"
            f"Active Tenant ID: {tenant_id}\n"
            "Low Stock & Reorder Points:\n"
            + ("\n".join(low_stock_summary) if low_stock_summary else "No active low stock alerts.")
            + "\n\nUnresolved Inventory Warnings:\n"
            + ("\n".join(alert_summary) if alert_summary else "Zero warnings.")
            + "\n===============================\n\n"
            "Maintain a professional, helpful, and concise medical tone."
        )
        
        # Initialize Gemini Model
        model = genai.GenerativeModel('gemini-pro')
        
        # Build prompt incorporating chat history
        prompt_parts = [system_context]
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            prompt_parts.append(f"{role_label}: {msg['content']}")
            
        prompt_parts.append(f"User: {message}")
        prompt_parts.append("Assistant:")
        
        # Generate response
        response = model.generate_content(prompt_parts)
        return response.text
        
    except Exception as e:
        return f"🔴 **Gemini AI error occurred:** {str(e)}"
