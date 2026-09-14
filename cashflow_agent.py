import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

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
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
    else:
        df = pd.read_csv("sample_data.csv") 

elif data_source == 'Manual Input Form':
    st.sidebar.info("4. Manual Input Form - For cash sales, future expected income/expenses")
    if 'manual_df' not in st.session_state:
        st.session_state.manual_df = pd.read_csv("sample_data.csv")
    
    with st.sidebar.form("manual_input", clear_on_submit=True):
        date = st.date_input("Date")
        income = st.number_input("Expected Income $", 0.0, step=100.0)
        expense = st.number_input("Expected Expense $", 0.0, step=100.0)
        submitted = st.form_submit_button("➕ Add Row")
        if submitted:
            new_row = pd.DataFrame({'Date':[date], 'Income':[income], 'Expenses':[expense]})
            st.session_state.manual_df = pd.concat([st.session_state.manual_df, new_row], ignore_index=True)
            st.success("Row Added!")
    df = st.session_state.manual_df

elif data_source == 'Connect Bank/API - Demo':
    st.sidebar.warning("1. Bank/API Connector: Demo Mode")
    st.sidebar.write("Connect to: Bank, Ecocash, PayPal, Stripe")
    st.sidebar.write("3. Invoice & AR/AP: Track who owes you")
    df = pd.read_csv("sample_data.csv")

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
forecast_df['Income'] = 0
forecast_df['Expenses'] = 0

# --- ALL TABS ---
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🔌 A. Data Inputs", 
    "📊 1. Dashboard", 
    "🚨 2. Alerts", 
    "📄 3. Report Generator", 
    "⚡ 4. Action Tools"
])

# TAB 0: DATA CONNECTORS
with tab0:
    st.header("A. Data Connectors / Inputs")
    st.write("**Current source:**", data_source)
    col1, col2, col3, col4 = st.columns(4)
    col1.success("1. Bank/API: Bank, Ecocash")
    col2.info("2. Accounting: Quickbooks, Xero, Excel")
    col3.warning("3. Invoice & AR/AP: Who Owes You")
    col4.success("4. Manual Input: Cash Sales")
    st.markdown("#### Current Data Table")
    st.dataframe(df, use_container_width=True)

# TAB 1: DASHBOARD
with tab1:
    st.header("Dashboard / Visualization - Next 90 Days")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cash In", f"${df['Income'].sum():,.2f}")
    col2.metric("Total Cash Out", f"${df['Expenses'].sum():,.2f}")
    col3.metric("Current Balance", f"${df['Cumulative Cash'].iloc[-1]:,.2f}")
    col4.metric("Projected 90 Days", f"${forecast_cumulative[-1]:,.2f}")

    st.markdown("#### Cash In vs Cash Out vs Projected Balance")
    fig1, ax1 = plt.subplots(figsize=(10,4))
    ax1.plot(df['Date'], df['Income'], label='Cash In', marker='o')
    ax1.plot(df['Date'], df['Expenses'], label='Cash Out', marker='o')
    ax1.plot(df['Date'], df['Cumulative Cash'], label='Historical Balance')
    ax1.plot(forecast_df['Date'], forecast_df['Cumulative Cash'], label='Projected 90 Days', linestyle='--', marker='x')
    ax1.legend(); ax1.grid(True); ax1.set_ylabel("Amount ($)")
    st.pyplot(fig1)

# TAB 2: ALERTS
with tab2:
    st.header("🚨 AI Alerts")
    alert_found = False
    for i, row in forecast_df.iterrows():
        if row['Cumulative Cash'] < 0:
            date_str = row['Date'].strftime('%b %d, %Y')
            st.error(f"Warning: You will be ${abs(row['Cumulative Cash']):,.0f} short on {date_str}")
            alert_found = True
        elif row['Cumulative Cash'] < last_cumulative * 0.5:
            date_str = row['Date'].strftime('%b %d, %Y')
            st.warning(f"Caution: Cash will drop below 50% by {date_str}")
            alert_found = True
    
    if not alert_found and forecast_cumulative[-1] > last_cumulative:
        st.success("✅ Healthy: Projected cash is increasing over next 90 days")

# TAB 3: REPORT GENERATOR - NO PDF, USES CSV
with tab3:
    st.header("📄 Weekly Cashflow Forecast Report")
    st.info("Download your report to upload to Google Sheets")
    
    report_df = pd.concat([df[['Date','Income','Expenses','Cumulative Cash']], forecast_df[['Date','Income','Expenses','Cumulative Cash']]])
    
    st.download_button(
        label="📥 Download Forecast CSV",
        data=report_df.to_csv(index=False).encode('utf-8'),
        file_name="cashflow_report.csv",
        mime="text/csv"
    )
    st.dataframe(report_df, use_container_width=True)

# TAB 4: ACTION TOOLS
with tab4:
    st.header("⚡ AI Action Tools")
    st.markdown("Based on your forecast, here are recommended actions:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✉️ Email Client to Pay Invoice"):
            st.success("Email template: 'Dear Client, Kindly settle your invoice to improve our cashflow. Thank you.'")
        if st.button("💰 Ways to Increase Income"):
            st.info("1. Run a promotion \n2. Follow up on receivables \n3. Offer discounts for upfront payment")
    
    with col2:
        if st.button("⏰ Suggest Delaying Expense"):
            st.warning("Action: Flag non-critical expenses for next 30 days")
        if st.button("📉 Ways to Cut Costs"):
            st.info("1. Negotiate with suppliers \n2. Delay equipment purchase \n3. Review subscriptions")
