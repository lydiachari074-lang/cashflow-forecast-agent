import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, date

st.set_page_config(page_title="AI Cash Flow Agent", layout="wide")
st.title("🤖 AI Cash Flow Forecasting Agent for SMEs")

# --- SIMULATED DATA FUNCTIONS ---
def load_sample_data():
    # Default data so we don't need sample_data.csv
    data = {
        'Date': pd.date_range(start='2025-05-01', periods=4, freq='ME'), # FIXED: ME not M
        'Income': [5000, 5300, 4800, 5500],
        'Expenses': [3000, 3100, 3500, 3200]
    }
    return pd.DataFrame(data)

def load_bank_data():
    # Simulates Bank API
    data = {
        'Date': pd.date_range(end=date.today(), periods=4, freq='ME'), # FIXED: ME not M
        'Income': [6000, 6500, 5800, 7200],
        'Expenses': [3200, 3500, 4000, 3800],
        'Source': ['Bank Transfer', 'Client Payment', 'Bank Transfer', 'Sales']
    }
    return pd.DataFrame(data)

def load_ecocash_data():
    # Simulates Ecocash API
    data = {
        'Date': pd.date_range(end=date.today(), periods=4, freq='ME'), # FIXED: ME not M
        'Income': [1500, 2200, 1800, 2500],
        'Expenses': [800, 1200, 900, 1100],
        'Source': ['Ecocash Merchant', 'Ecocash Send', 'Ecocash Cash-in', 'Ecocash Payment']
    }
    return pd.DataFrame(data)

# --- SESSION STATE TO REMEMBER DATA ---
if 'df' not in st.session_state:
    st.session_state.df = load_sample_data()
if 'data_source' not in st.session_state:
    st.session_state.data_source = 'Upload CSV/Excel'

# --- SIDEBAR ---
st.sidebar.header("A. Data Connectors / Inputs")

data_source = st.sidebar.radio(
    "1. Choose Data Source:",
    ('Upload CSV/Excel', 'Manual Input Form', 'Connect Bank', 'Connect Ecocash'),
    key='source_radio'
)
st.session_state.data_source = data_source

if data_source == 'Upload CSV/Excel':
    uploaded_file = st.sidebar.file_uploader("Upload from Excel/Sheets", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.success("File Uploaded!")
        st.rerun()

elif data_source == 'Manual Input Form':
    st.sidebar.info("For cash sales, future expected income/expenses")
    if 'manual_df' not in st.session_state:
        st.session_state.manual_df = load_sample_data()
    
    with st.sidebar.form("manual_input", clear_on_submit=True):
        date_in = st.date_input("Date")
        income = st.number_input("Expected Income $", 0.0, step=100.0)
        expense = st.number_input("Expected Expense $", 0.0, step=100.0)
        submitted = st.form_submit_button("➕ Add Row")
        if submitted:
            new_row = pd.DataFrame({'Date':[date_in], 'Income':[income], 'Expenses':[expense]})
            st.session_state.manual_df = pd.concat([st.session_state.manual_df, new_row], ignore_index=True)
            st.session_state.df = st.session_state.manual_df
            st.success("Row Added!")
            st.rerun()

elif data_source == 'Connect Bank':
    st.sidebar.success("✅ Bank Account Connected - Demo Mode")
    st.sidebar.info("In real app: Uses Bank API to pull transactions")
    if st.sidebar.button("🔄 Sync Latest Bank Transactions"):
        st.session_state.df = load_bank_data()
        st.success("Bank transactions synced!")
        st.rerun()

elif data_source == 'Connect Ecocash':
    st.sidebar.success("✅ Ecocash Account Connected - Demo Mode")
    st.sidebar.info("In real app: Uses Ecocash API to pull merchant payments")
    if st.sidebar.button("🔄 Sync Latest Ecocash Transactions"):
        st.session_state.df = load_ecocash_data()
        st.success("Ecocash transactions synced!")
        st.rerun()

df = st.session_state.df

# --- PROCESS DATA & FORECAST ---
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')
df['Net Cash Flow'] = df['Income'] - df['Expenses']
df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()

avg_net_cash = df['Net Cash Flow'].mean()
last_date = df['Date'].iloc[-1]
last_cumulative = df['Cumulative Cash'].iloc[-1]
forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]
forecast_cumulative = [last_cumulative + avg_net_cash*i for i in range(1, 4)]
forecast_df = pd.DataFrame({'Date': forecast_dates, 'Cumulative Cash': forecast_cumulative, 'Income':0, 'Expenses':0})

# --- 5 TABS FOR ALL COMPONENTS ---
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🔌 A. Data Inputs", "📊 1. Dashboard", "🚨 2. AI Alerts", "📄 3. Report", "⚡ 4. Action Tools"
])

with tab0:
    st.header("A. Data Connectors / Inputs")
    st.write("**Current source:**", st.session_state.data_source)
    col1, col2, col3, col4 = st.columns(4)
    col1.success("1. Bank/API: Connected")
    col2.info("2. Accounting: Quickbooks, Xero, Excel")
    col3.warning("3. Invoice & AR/AP: Who Owes You")
    col4.success("4. Manual Input: Cash Sales")
    st.markdown("#### Current Data Table")
    st.dataframe(df, use_container_width=True)

with tab1:
    st.header("Dashboard / AI Forecast - Next 90 Days")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cash In", f"${df['Income'].sum():,.2f}")
    col2.metric("Total Cash Out", f"${df['Expenses'].sum():,.2f}")
    col3.metric("Current Balance", f"${df['Cumulative Cash'].iloc[-1]:,.2f}")
    col4.metric("Projected 90 Days", f"${forecast_cumulative[-1]:,.2f}")

    fig1, ax1 = plt.subplots(figsize=(10,4))
    ax1.plot(df['Date'], df['Cumulative Cash'], label='Historical Balance', marker='o')
    ax1.plot(forecast_df['Date'], forecast_df['Cumulative Cash'], label='AI Forecast 90 Days', linestyle='--', marker='x')
    ax1.legend(); ax1.grid(True); ax1.set_ylabel("Amount ($)")
    st.pyplot(fig1)

with tab2:
    st.header("🚨 AI Alerts")
    alert_found = False
    for i, row in forecast_df.iterrows():
        if row['Cumulative Cash'] < 0:
            st.error(f"⚠️ Shortfall Alert: You will be ${abs(row['Cumulative Cash']):,.0f} short on {row['Date'].strftime('%b %d, %Y')}")
            alert_found = True
    if not alert_found:
        st.success("✅ Healthy: No projected cash shortfall in next 90 days")

with tab3:
    st.header("📄 Report Generator")
    report_df = pd.concat([df[['Date','Income','Expenses','Cumulative Cash']], forecast_df[['Date','Income','Expenses','Cumulative Cash']]])
    st.download_button(
        label="📥 Download Forecast CSV",
        data=report_df.to_csv(index=False).encode('utf-8'),
        file_name="cashflow_report.csv",
        mime="text/csv"
    )
    st.dataframe(report_df, use_container_width=True)

with tab4:
    st.header("⚡ AI Action Tools")
    st.markdown("Based on your forecast, here are recommended actions:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✉️ Email Client to Pay Invoice"):
            st.success("Template: 'Dear Client, Kindly settle your invoice to improve our cashflow. Thank you.'")
        if st.button("💰 Ways to Increase Income"):
            st.info("1. Run a promotion \n2. Follow up on receivables \n3. Offer discounts for upfront payment")
    with col2:
        if st.button("⏰ Suggest Delaying Expense"):
            st.warning("Action: Flag non-critical expenses for next 30 days")
        if st.button("📉 Ways to Cut Costs"):
            st.info("1. Negotiate with suppliers \n2. Delay equipment purchase \n3. Review subscriptions")
