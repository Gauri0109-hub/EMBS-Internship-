# Smart Pharmacy Inventory Prediction System 🩺🔮
### *An Advanced, Explainable Healthcare AI Dashboard for Rural Clinics and Small Pharmacies*

---

## 🌟 Project Overview
In rural India, Primary Health Centres (PHCs) and local pharmacies operate under tight budgets. They frequently face severe stock-outs of life-saving, critical medicines (like Insulin, Asthma Inhalers, or Epilepsy drugs) due to unexpected seasonal illness surges (like dengue fevers during the monsoon or respiratory cases in winter). Conversely, over-stocking other medicines results in capital loss when formulations expire on shelves unnoticed.

This **Smart Pharmacy Inventory Prediction System** is a fully functional, complete, and production-ready Python & Streamlit application. It implements explainable machine learning models (**Linear Regression** and **Random Forest Regressor**) to forecast 30-day daily medicine consumption, predict exact stock-out dates, issue color-coded risk alerts, and generate automated restocking orders with estimated billing.

The application contains **7 fully structured pages** in a highly aesthetic, clean, and modern healthcare-themed UI, supporting **Bilingual labels (English + Marathi)** for rural clinic accessibility.

---

## 📁 Project Folder Structure
The workspace is organized cleanly as follows:
```text
EMBS internship/
├── data/
│   ├── medicine_inventory.csv       # 25 common medicine formulations with metadata
│   └── daily_usage_history.csv      # 365 days of chronological sales logs (9,150 entries)
├── src/
│   ├── __init__.py
│   ├── data_generator.py            # Generates realistic synthetic clinical databases
│   ├── ml_model.py                  # ML Engine (LR & Random Forest) for forecasts & stock-outs
│   └── app.py                       # Main 7-page interactive dashboard web application
├── requirements.txt                 # Project dependencies list
├── README.md                        # Complete user & developer setup guide (This file)
└── PRESENTATION.md                  # PowerPoint outline, speaker notes, and Viva Q&A prep sheets
```

---

## 📑 Streamlit Dashboard Page Breakdown

The dashboard is structured into **7 interactive pages** accessible from the clean sidebar menu:

### 1. 🏠 Home Dashboard
* **KPI Metrics Panel:** High-impact cards summarizing Total Formulations, Critical Life-saving Drugs, Low Stock Warnings, and Urgent Out-of-Stock alerts.
* **Interactive Chart:** A Plotly bar chart comparing every medicine's current shelf stock side-by-side with its safety reorder point.
* **Instruction Cards:** Quick guidelines for clinic operators on handling Red, Yellow, and Green alerts.

### 2. 📦 Inventory Management
* **Active Database Table:** Displays all 25 medicines with search and category filters.
* **Add New Medicine Form:** Full form to append a new formulation to the database.
* **Update Stock Level Form:** Easily change stock quantities of shelf stock.
* **Delete Medicine Form:** Allows permanent removal of a medicine from the database with double-check confirmation boxes.
* *All changes persist instantly to `data/medicine_inventory.csv`.*

### 3. 🔮 Prediction Analytics (AI Forecasts)
* **ML Model Selector:** Instantly toggle between **Linear Regression** and **Random Forest Regressor** to compare forecasting.
* **Depletion Panel:** Displays the estimated Stock-Out Date, remaining days of stock, and active risk level.
* **Interactive Plotly Graph:** Projects the last 60 days of historical sales alongside a 30-day daily demand forecast represented as a dashed orange line.
* **Viva Explainer:** Dedicated explainability card helping students explain the mathematical logic during project reviews.

### 4. ⚠️ Alerts & Risks
* **Red Stockout Alarms:** Formulations likely to deplete in $\le 7$ days.
* **Yellow Warnings:** Formulations with 8–15 days of stock remaining.
* **Critical Drug Watchdog:** Dedicated panel highlighting life-saving medications (Insulin, Asthma inhalers, Epilepsy drugs) to ensure pharmacists never overlook them.
* **Expiry Monitoring:** Dedicated tables separating completely **Expired** drugs (discard immediately) and drugs **Expiring Soon** ($<30$ days).

### 5. 🍂 Seasonal Insights
* **Epidemiological Analysis:** Outline of Indian disease seasonality (Monsoon fever spikes, Winter cold surges, Summer dehydration spikes).
* **Grouped Bar Graph:** Plotly chart displaying the average daily usage of medicine categories across different seasons (Monsoon, Winter, Summer).
* **Seasonal Filter:** Easily filter the database to view high-consumption formulations for a chosen season.

### 6. 📈 Medicine Trends
* **Overlay Trends Line Graph:** Overlay and compare historical demand timelines for multiple selected formulations simultaneously.
* **Category Distribution Chart:** A Plotly pie chart highlighting shelf allocation shares across therapeutic categories.
* **Risk Level Heatmap:** A visual summary count of Green, Yellow, and Red status medicines.

### 7. 📄 Reports & Exports
* **AI Restocking Recommendation Sheet:** Auto-generates exact order quantities (`30-day forecast + 8-day safety buffer - current stock`) sorted with **Critical Medicines on top**, complete with supplier contacts.
* **Cost Estimations:** Displays total procurement counts and billing estimates.
* **Download Buttons:** Download the complete **Inventory Status** or **AI Restocking Sheet** directly as CSV files.
* **Copyable Clinic Report:** Renders a clean text-based receipt suitable for clinical printouts.

---

## 🛠️ Step-by-Step Setup Guide

### Step 1: Open project directory
Ensure all files are placed in your working folder (e.g. `EMBS internship`).

### Step 2: Install dependencies
Open your terminal or command prompt in the project root directory and execute:
```bash
pip install -r requirements.txt
```
This installs Streamlit, Pandas, NumPy, scikit-learn, and Plotly.

### Step 3: Run the Dashboard App
Run the Streamlit server:
```bash
streamlit run src/app.py
```
This will automatically launch the dashboard in your default web browser (typically at `http://localhost:8501`).

*Note: On first startup, the app will automatically invoke `src/data_generator.py` to create the initial CSV datasets inside the `data/` folder. You can also trigger this manually by running `python src/data_generator.py`.*

---

## 🧠 Explainability: How the AI Works

### 1. The Historical Clinical Database
* `data/daily_usage_history.csv` simulates 9,150 entries (365 days of transactions for 25 medicines).
* Monsoonal fevers are simulated with high multipliers for Paracetamol and antibiotics. Winter is simulated with higher cold syrup and Salbutamol inhaler usage. Summer has 3x rehydration salts demand. Metformin and Insulin Glargine remain constant all year.

### 2. Feature Engineering
In `ml_model.py`, dates are converted to numerical inputs scikit-learn can read:
- `month` (1 to 12)
- `day_of_week` (0 to 6)
- `is_summer`, `is_monsoon`, `is_winter` (binary flags representing seasons)
- `rolling_avg` (the average usage of the past 7 days, capturing current momentum).

### 3. The Forecasting Models
* **Linear Regression:** Models linear trends using weighted coefficients:
  $$\text{Daily Demand} = w_1 \cdot \text{Month} + w_2 \cdot \text{DayOfWeek} + w_3 \cdot \text{Monsoon} + ... + c$$
  Perfect for showcasing basic seasonal variables in presentations.
* **Random Forest Regressor:** Combines predictions from multiple decision trees. This is ideal for catching rapid spikes and complex interactions during sudden disease outbreaks.

### 4. Stock-Out Depletion Algorithm
To locate the exact stock-out date:
1. The app trains the chosen ML model specifically on the history of the selected medicine.
2. It forecasts the exact daily demand for each of the next 30 days.
3. It runs a simulation starting with the current shelf stock and subtracting the predicted usage day-by-day.
4. The exact date the stock falls to $\le 0$ is flagged as the **Predicted Stock-Out Date**.

---

## 🔮 Future Scope
* **SQLite Backend:** Upgrade from CSV files to a lightweight SQLite database to prevent multi-terminal conflicts.
* **Automatic SMS Alerts:** Integrate a messaging API (like Twilio) to automatically text local medical distributors when stock level hits the red zone.
* **Epidemiological Integration:** Syncing dashboard insights with national disease surveillance centers to automatically alert clinics of emerging local epidemics.

---

## 🤝 Project Credits
* Developed for **EMBS Internship Review** and **Beginner Engineering Presentations**.
* Built using Python, Streamlit, scikit-learn, and Plotly. Fully modular and runnable offline.
