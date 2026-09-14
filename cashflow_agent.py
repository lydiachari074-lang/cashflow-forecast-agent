import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, date

st.set_page_config(page_title="AI Cash Flow Agent", layout="wide")
st.title("🤖 AI Cash Flow Forecasting Agent for SMEs")

# --- SIMULATED DATA FUNCTIONS ---
def load_bank_data():
    data = {
        'Date': pd.date_range(end=date.today(), periods=4, freq='M'),
        'Income': [6000, 6500, 5800, 7200],
        'Expenses': [3200, 3500, 4000, 3800],
        'Source': ['Bank Transfer', 'Client Payment', 'Bank Transfer', 'Sales']
    }
    return pd.DataFrame(data)

def load_ecocash_data():
    data = {
        'Date': pd.date_range(end=date.today(), periods=4, freq='M'),
        'Income': [1500, 2200, 1800, 2500],
        'Expenses': [800, 1200, 900, 1100],
        'Source': ['Ecocash Merchant', 'Ecocash Send', 'Ecocash Cash-in', 'Ecocash Payment']
    }
    return pd.DataFrame(data)

def load_sample_data():
    return pd.read_csv("sample_data.csv")

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

df = st.session_state.df

if data_source == 'Upload CSV/Excel':
    uploaded_file = st.sidebar.file_uploader("Upload from Excel/Sheets", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file, engine='openpyxl')
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
    df = st.session_state.df

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

# --- TABS ---
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
    ax1.plot(df['Date'], df['Cumulative Cash'], label='Historical Balance')
    ax1.plot(forecast_df['Date'], forecast_df['Cumulative Cash'], label='AI Forecast 90 Days', linestyle='--', marker='x')
    ax1.legend(); ax1.grid(True); ax1.set_ylabel("Amount ($)")
    st.pyplot(fig1)

with tab2:
    st.header("🚨 AI Alerts")
    for i, row in forecast_df.iterrows():
        if row['Cumulative Cash'] < 0:
            st.error(f"Warning: You will be ${abs(row['Cumulative Cash']):,.0f} short on {row['Date'].strftime('%b %d')}")

with tab3:
    st.header("📄 Report Generator")
    report_df = pd.concat([df, forecast_df])
    st.download_button("📥 Download Forecast CSV", data=report_df.to_csv(index=False).encode('utf-8'), file_name="cashflow_report.csv")

with tab4:
    st.header("⚡ AI Action Tools")
    st.button("✉️ Email Client to Pay Invoice")
    st.button("⏰ Suggest Delaying Expense")
