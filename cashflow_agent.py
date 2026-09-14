import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Cash Flow Agent", layout="wide")
st.title("🤖 AI Cash Flow Forecasting Agent for SMEs")

# --- SIDEBAR = Makes it look professional ---
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV: Date, Income, Expenses", type=["csv"])
st.sidebar.info("This AI Agent helps SMEs forecast cash, assess risk, and get recommendations.")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv("sample_data.csv") 

df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')
df['Net Cash Flow'] = df['Income'] - df['Expenses']
df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()

# --- TABS = THIS IS YOUR DASHBOARD ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Forecast", "⚠️ Risk & Recommendations"])

with tab1:
    st.header("Dashboard Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Income", f"${df['Income'].sum():,.2f}")
    col2.metric("Total Expenses", f"${df['Expenses'].sum():,.2f}")
    col3.metric("Avg Monthly Net", f"${df['Net Cash Flow'].mean():,.2f}")
    col4.metric("Current Cash", f"${df['Cumulative Cash'].iloc[-1]:,.2f}")

    st.markdown("#### Income vs Expenses Trend")
    fig1, ax1 = plt.subplots()
    ax1.plot(df['Date'], df['Income'], label='Income')
    ax1.plot(df['Date'], df['Expenses'], label='Expenses')
    ax1.legend()
    st.pyplot(fig1)

    st.dataframe(df, use_container_width=True)

with tab2:
    st.header("3-Month Cash Flow Forecast")
    avg_net_cash = df['Net Cash Flow'].mean()
    last_date = df['Date'].iloc[-1]
    last_cumulative = df['Cumulative Cash'].iloc[-1]
    forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]
    forecast_cumulative = [last_cumulative + avg_net_cash*i for i in range(1, 4)]
    forecast_df = pd.DataFrame({'Date': forecast_dates, 'Cumulative Cash': forecast_cumulative})

    fig2, ax2 = plt.subplots()
    ax2.plot(df['Date'], df['Cumulative Cash'], label='Historical')
    ax2.plot(forecast_df['Date'], forecast_df['Cumulative Cash'], label='Forecast', linestyle='--')
    ax2.legend()
    st.pyplot(fig2)
    st.dataframe(forecast_df)

with tab3:
    st.header("AI Risk Assessment & Recommendations")
    last_forecast_cash = forecast_df['Cumulative Cash'].iloc[-1]
    if last_forecast_cash < 0:
        st.error("🔴 AT RISK: Projected cash is negative")
        st.write("1. Reduce Expenses \n2. Increase Income \n3. Secure Funding")
    elif last_forecast_cash < df['Cumulative Cash'].iloc[-1] * 0.5:
        st.warning("🟡 CAUTION: Cash dropping significantly")
        st.write("1. Monitor Weekly \n2. Delay Purchases \n3. Negotiate Terms")
    else:
        st.success("🟢 HEALTHY: Cash position stable")
        st.write("1. Reinvest \n2. Build Reserve \n3. Plan Expansion")
