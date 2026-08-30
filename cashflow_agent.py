import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Cash Flow Forecasting Agent", layout="wide")
st.title("💰 AI Cash Flow Forecasting Agent")
st.write("Upload your income and expense data. The agent will forecast cash flow and flag risks.")

# STEP 1: READ INPUT
uploaded_file = st.file_uploader("Upload CSV with columns: Date, Income, Expenses", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Net Cash Flow'] = df['Income'] - df['Expenses']
    df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()
    
    st.subheader("1. Your Data Analysis")
    st.dataframe(df)
    
    # STEP 2: ANALYZE + FORECAST
    st.subheader("2. 3-Month Cash Flow Forecast")
    
    avg_income = df['Income'].mean()
    avg_expense = df['Expenses'].mean()
    last_cumulative = df['Cumulative Cash'].iloc[-1]
    last_date = df['Date'].iloc[-1]
    
    forecast_dates = [last_date + timedelta(days=30*i) for i in range(1,4)]
    forecast_net = [avg_income - avg_expense] * 3
    forecast_cumulative = []
    
    running_total = last_cumulative
    for net in forecast_net:
        running_total += net
        forecast_cumulative.append(running_total)
    
    forecast_df = pd.DataFrame({
        'Date': forecast_dates,
        'Forecasted Net Cash Flow': forecast_net,
        'Forecasted Cumulative Cash': forecast_cumulative
    })
    
    st.dataframe(forecast_df)
    
    # STEP 3: DECIDE / FLAG
    st.subheader("3. Risk Assessment")
    if forecast_cumulative[-1] < 0:
        st.error("🚨 CASH SHORTAGE RISK: Forecast shows negative cash in 3 months. Recommendation: Reduce expenses or secure funding.")
    elif forecast_cumulative[-1] < last_cumulative * 0.5:
        st.warning("⚠️ WARNING: Cash is projected to drop by over 50%. Recommendation: Review spending.")
    else:
        st.success("✅ HEALTHY: Cash position is projected to remain stable.")
    
    # STEP 4: PRODUCE OUTPUT - CHART
    st.subheader("4. Cash Flow Visualization")
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(df['Date'], df['Cumulative Cash'], label='Historical Cash', marker='o')
    ax.plot(forecast_df['Date'], forecast_df['Forecasted Cumulative Cash'], label='Forecast', linestyle='--', marker='x')
    ax.axhline(0, color='red', linestyle=':')
    ax.set_ylabel("Cumulative Cash")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

else:
    st.info("Please upload a CSV or Excel file to start the agent.")
    st.write("**Sample format:** Date, Income, Expenses")