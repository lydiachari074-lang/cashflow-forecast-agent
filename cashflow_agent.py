import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas

st.set_page_config(page_title="AI Cash Flow Agent", layout="wide")
st.title("🤖 AI Cash Flow Forecasting Dashboard Agent for SMEs")

# --- 1. CORE EXTRA COMPONENTS: DATA CONNECTORS / INPUTS ---
st.sidebar.header("A. Data Connectors / Inputs")

data_source = st.sidebar.radio(
    "1. Choose Data Source:",
    ('Upload CSV/Excel', 'Manual Input Form', 'Connect Bank/API - Demo')
)

df = pd.DataFrame()

if data_source == 'Upload CSV/Excel':
    uploaded_file = st.sidebar.file_uploader("2. Accounting System: Upload from Excel/Sheets", type=["csv", "xlsx"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv("sample_data.csv") 

elif data_source == 'Manual Input Form':
    st.sidebar.info("4. Manual Input Form - For cash sales, future expected income/expenses")
    with st.sidebar.form("manual_input"):
        date = st.date_input("Date")
        income = st.number_input("Expected Income $", 0)
        expense = st.number_input("Expected Expense $", 0)
        submitted = st.form_submit_button("Add Row")
        if submitted:
            new_row = pd.DataFrame({'Date':[date], 'Income':[income], 'Expenses':[expense]})
            if 'manual_df' not in st.session_state:
                st.session_state.manual_df = pd.read_csv("sample_data.csv")
            st.session_state.manual_df = pd.concat([st.session_state.manual_df, new_row], ignore_index=True)
    df = st.session_state.get('manual_df', pd.read_csv("sample_data.csv"))

elif data_source == 'Connect Bank/API - Demo':
    st.sidebar.warning("1. Bank/API Connector: Demo Mode")
    st.sidebar.write("Connect to: Bank, Ecocash, PayPal, Stripe")
    st.sidebar.write("3. Invoice & AR/AP: Track who owes you")
    df = pd.read_csv("sample_data.csv") # In real app this would pull from API

# --- PROCESS DATA ---
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')
df['Net Cash Flow'] = df['Income'] - df['Expenses']
df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()

avg_net_cash = df['Net Cash Flow'].mean()
last_date = df['Date'].iloc[-1]
last_cumulative = df['Cumulative Cash'].iloc[-1]
forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]
forecast_cumulative = [last_cumulative + avg_net_cash*i for i in range(1, 4)]
forecast_df = pd.DataFrame({'Date': forecast_dates, 'Cumulative Cash': forecast_cumulative})

# --- ALL OUR EXISTING TABS + 2 NEW ONES ---
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🔌 A. Data Inputs", 
    "📊 1. Dashboard", 
    "🚨 2. Alerts", 
    "📄 3. Report Generator", 
    "⚡ 4. Action Tools"
])

# TAB 0: SHOW DATA CONNECTORS
with tab0:
    st.header("A. Data Connectors / Inputs")
    st.write("The agent needs to see your real money. Current source:", data_source)
    col1, col2, col3, col4 = st.columns(4)
    col1.success("1. Bank/API: Ecocash, Bank")
    col2.info("2. Accounting: Quickbooks, Xero, Excel")
    col3.warning("3. Invoice & AR/AP: Who Owes You")
    col4.success("4. Manual Input: Cash Sales")
    st.dataframe(df, use_container_width=True)

# TAB 1: DASHBOARD - KEEPING WHAT WE ALREADY DID
with tab1:
    st.header("Dashboard / Visualization - Next 90 Days")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cash In", f"${df['Income'].sum():,.2f}")
    col2.metric("Total Cash Out", f"${df['Expenses'].sum():,.2f}")
    col3.metric("Current Balance", f"${df['Cumulative Cash'].iloc[-1]:,.2f}")
    col4.metric("Projected 90 Days", f"${forecast_cumulative[-1]:,.2f}")

    fig1, ax1 = plt.subplots(figsize=(10,4))
    ax1.plot(df['Date'], df['Income'], label='Cash In')
    ax1.plot(df['Date'], df['Expenses'], label='Cash Out')
    ax1.plot(df['Date'], df['Cumulative Cash'], label='Historical Balance')
    ax1.plot(forecast_df['Date'], forecast_df['Cumulative Cash'], label='Projected 90 Days', linestyle='--')
    ax1.legend(); ax1.grid(True)
    st.pyplot(fig1)

# TAB 2: ALERTS - KEEPING WHAT WE ALREADY DID
with tab2:
    st.header("🚨 AI Alerts")
    for i, row in forecast_df.iterrows():
        if row['Cumulative Cash'] < 0:
            date_str = row['Date'].strftime('%b %d')
            st.error(f"Warning: You will be ${abs(row['Cumulative Cash']):,.0f} short on {date_str}")
    if forecast_cumulative[-1] > last_cumulative:
        st.success("✅ Healthy: Projected cash is increasing over next 90 days")

# TAB 3: REPORT - KEEPING WHAT WE ALREADY DID
with tab3:
    st.header("📄 Weekly Cashflow Forecast Report")
    def create_pdf():
        buffer = BytesIO(); c = canvas.Canvas(buffer)
        c.drawString(100, 800, "AI Cash Flow Forecast Report"); c.save(); buffer.seek(0); return buffer
    st.download_button("📥 Download Forecast PDF", data=create_pdf(), file_name="cashflow_report.pdf")
    st.dataframe(pd.concat([df, forecast_df]), use_container_width=True)

# TAB 4: ACTION TOOLS - KEEPING WHAT WE ALREADY DID
with tab4:
    st.header("⚡ AI Action Tools")
    st.button("✉️ Email Client to Pay Invoice")
    st.button("⏰ Suggest Delaying This Expense")
