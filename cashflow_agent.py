import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, date

st.set_page_config(page_title="AI Cash Flow Agent", layout="wide")
st.title("🤖 AI Cash Flow Forecasting Agent for SMEs")

# --- SIMULATED DATA FUNCTIONS ---
def load_sample_data():
    data = {
        'Date': pd.date_range(start='2025-05-01', periods=4, freq='ME'),
        'Income': [5000, 5300, 4800, 5500],
        'Expenses': [3000, 3100, 3500, 3200]
    }
    return pd.DataFrame(data)

def load_bank_data():
    data = {
        'Date': pd.date_range(end=date.today(), periods=4, freq='ME'),
        'Income': [6000, 6500, 5800, 7200],
        'Expenses': [3200, 3500, 4000, 3800],
        'Source': ['Bank Transfer', 'Client Payment', 'Bank Transfer', 'Sales']
    }
    return pd.DataFrame(data)

def load_ecocash_data():
    data = {
        'Date': pd.date_range(end=date.today(), periods=4, freq='ME'),
        'Income': [1500, 2200, 1800, 2500],
        'Expenses': [800, 1200, 900, 1100],
        'Source': ['Ecocash Merchant', 'Ecocash Send', 'Ecocash Cash-in', 'Ecocash Payment']
    }
    return pd.DataFrame(data)

# --- SESSION STATE ---
if 'df' not in st.session_state:
    st.session_state.df = load_sample_data()
if 'data_source' not in st.session_state:
    st.session_state.data_source = 'Upload CSV/Excel'
if 'forecast_model' not in st.session_state:
    st.session_state.forecast_model = 'Simple Moving Average'
if 'scenario' not in st.session_state:
    st.session_state.scenario = 'Base Case'

df = st.session_state.df

# --- SIDEBAR A. DATA CONNECTORS ---
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
    if st.sidebar.button("🔄 Sync Latest Bank Transactions"):
        st.session_state.df = load_bank_data()
        st.success("Bank transactions synced!")
        st.rerun()

elif data_source == 'Connect Ecocash':
    st.sidebar.success("✅ Ecocash Account Connected - Demo Mode")
    if st.sidebar.button("🔄 Sync Latest Ecocash Transactions"):
        st.session_state.df = load_ecocash_data()
        st.success("Ecocash transactions synced!")
        st.rerun()

# --- PROCESS DATA ---
df = st.session_state.df
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')
df['Net Cash Flow'] = df['Income'] - df['Expenses']
df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()

# --- B. FORECASTING ENGINE ---
st.sidebar.header("B. Forecasting Engine / Tools")
st.sidebar.write("The LLM tells it what to do, code does the calculation")

st.session_state.forecast_model = st.sidebar.selectbox(
    "1. Time-series Model",
    ['Simple Moving Average', 'Prophet Simulation', 'ARIMA Simulation']
)

# 2. Rules Engine
st.sidebar.subheader("2. Rules Engine")
rent_due = st.sidebar.checkbox("Rent due every 1st: $1500", True)
salaries_due = st.sidebar.checkbox("Salaries on 25th: $3000", True)

# 3. Scenario Simulator
st.session_state.scenario = st.sidebar.selectbox(
    "3. Scenario Simulator",
    ['Base Case', 'Sales drop 20%', 'Loan $10000 comes in']
)

# --- CALCULATE FORECAST ---
avg_net_cash = df['Net Cash Flow'].mean()

# Apply Rules Engine
if rent_due: avg_net_cash -= 1500/30 # spread rent over month
if salaries_due: avg_net_cash -= 3000/30 # spread salaries

# Apply Scenario
if st.session_state.scenario == 'Sales drop 20%':
    avg_net_cash = avg_net_cash * 0.8
elif st.session_state.scenario == 'Loan $10000 comes in':
    avg_net_cash = avg_net_cash + 10000/3

last_date = df['Date'].iloc[-1]
last_cumulative = df['Cumulative Cash'].iloc[-1]
forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]
forecast_cumulative = [last_cumulative + avg_net_cash*i for i in range(1, 4)]
forecast_df = pd.DataFrame({'Date': forecast_dates, 'Cumulative Cash': forecast_cumulative})

# --- 5 TABS ---
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🔌 A. Data Inputs", "⚙️ B. Forecasting Engine", "📊 C. Dashboard", "🚨 D. AI Alerts", "⚡ E. Action Tools"
])

with tab0:
    st.header("A. Data Connectors / Inputs")
    st.write("**Current source:**", st.session_state.data_source)
    col1, col2, col3, col4 = st.columns(4)
    col1.success("1. Bank/API")
    col2.info("2. Accounting: Excel/CSV")
    col3.warning("3. Invoice & AR/AP")
    col4.success("4. Manual Input")
    st.dataframe(df, use_container_width=True)

with tab1: # NEW TAB FOR B
    st.header("B. Forecasting Engine / Tools")
    st.markdown("""
    **The LLM tells it what to do, but you need code to actually calculate.**
    
    **1. Time-series Model**: `{}` - Used for predicting inflows/outflows
    
    **2. Rules Engine**: Applied automatic rules like Rent and Salaries
    
    **3. Scenario Simulator**: Current scenario = **{}**
    - "What if sales drop 20%?" 
    - "What if loan comes in?"
    
    **4. Calculator Tool**: `Net Cashflow = Cash In - Cash Out`
    """.format(st.session_state.forecast_model, st.session_state.scenario))

with tab2:
    st.header("C. Dashboard / AI Forecast - Next 90 Days")
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

with tab3:
    st.header("D. AI Alerts")
    alert_found = False
    for i, row in forecast_df.iterrows():
        if row['Cumulative Cash'] < 0:
            st.error(f"⚠️ Shortfall Alert: You will be ${abs(row['Cumulative Cash']):,.0f} short on {row['Date'].strftime('%b %d, %Y')}")
            alert_found = True
    if not alert_found:
        st.success("✅ Healthy: No projected cash shortfall in next 90 days")

with tab4:
    st.header("E. AI Action Tools")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✉️ Email Client to Pay Invoice"):
            st.success("Template: 'Dear Client, Kindly settle your invoice to improve our cashflow.'")
    with col2:
        if st.button("⏰ Suggest Delaying Expense"):
            st.warning("Action: Flag non-critical expenses for next 30 days")
