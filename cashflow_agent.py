import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Cash Flow Forecasting Agent", layout="wide")
st.title("🤖 Cash Flow Forecasting Agent")

# --- FINANCE AGENT WORKFLOW ---
st.markdown("### 🤖 Finance Agent Workflow")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.success("**Step 1**\n\n📥 Read & Analyze Data")
with col2:
    st.success("**Step 2**\n\n📈 Generate 3-Month Forecast")
with col3:
    st.success("**Step 3**\n\n⚠️ Assess Financial Risk")
with col4:
    st.success("**Step 4**\n\n📊 Visualize Results")

st.markdown("---")
st.info("This agent autonomously ingests data, forecasts cash flow, assesses risk, and presents insights.")

# --- STEP 1: READ & ANALYZE DATA ---
st.markdown("### Step 1: Read & Analyze Data")

uploaded_file = st.file_uploader("Upload your CSV file with columns: Date, Income, Expenses", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv("sample_data.csv")  # fallback if no upload
    st.info("Using sample_data.csv. Upload your own file to test.")

# Convert Date column
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')

# Calculate Net Cash Flow and Cumulative Cash
df['Net Cash Flow'] = df['Income'] - df['Expenses']
df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()

st.dataframe(df, use_container_width=True)

# Summary Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"${df['Income'].sum():,.2f}")
col2.metric("Total Expenses", f"${df['Expenses'].sum():,.2f}")
col3.metric("Current Cash Balance", f"${df['Cumulative Cash'].iloc[-1]:,.2f}")

# --- STEP 2: GENERATE 3-MONTH FORECAST ---
st.markdown("### Step 2: Generate 3-Month Forecast")

# Use average net cash flow for forecast
avg_net_cash = df['Net Cash Flow'].mean()
last_date = df['Date'].iloc[-1]
last_cumulative = df['Cumulative Cash'].iloc[-1]

# Create forecast for next 3 months
forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]
forecast_net = [avg_net_cash] * 3
forecast_cumulative = []

running_total = last_cumulative
for net in forecast_net:
    running_total += net
    forecast_cumulative.append(running_total)

forecast_df = pd.DataFrame({
    'Date': forecast_dates,
    'Net Cash Flow': forecast_net,
    'Cumulative Cash': forecast_cumulative
})

st.write(f"**Forecasted Net Cash Flow for next 3 months: ${avg_net_cash * 3:,.2f}**")
st.dataframe(forecast_df, use_container_width=True)

# --- STEP 4: VISUALIZE RESULTS ---
st.markdown("### Step 4: Visualize Cash Flow")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df['Date'], df['Cumulative Cash'], label='Historical Cumulative Cash', marker='o')
ax.plot(forecast_df['Date'], forecast_df['Cumulative Cash'], label='Forecasted Cumulative Cash', marker='x', linestyle='--')
ax.set_xlabel('Date')
ax.set_ylabel('Cumulative Cash ($)')
ax.set_title('Cash Flow Trend + 3-Month Forecast')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# --- STEP 3: ASSESS FINANCIAL RISK & RECOMMENDATIONS ---
st.markdown("### Step 3: Assess Financial Risk & Recommendations")

last_forecast_cash = forecast_df['Cumulative Cash'].iloc[-1]
last_actual_cash = df['Cumulative Cash'].iloc[-1]

col1, col2 = st.columns(2)
with col1:
    st.metric("Current Cash Balance", f"${last_actual_cash:,.2f}")
with col2:
    st.metric("Forecasted Cash in 3 Months", f"${last_forecast_cash:,.2f}")

# Risk Assessment Logic
st.markdown("#### Risk Assessment")
if last_forecast_cash < 0:
    st.error("🔴 **RISK CONDITION FLAGGED: AT RISK**")
    st.write("Projected cumulative cash is negative. The business may run out of cash in the next 3 months.")
    risk_level = "AT RISK"
elif last_forecast_cash < last_actual_cash * 0.5:
    st.warning("🟡 **RISK CONDITION FLAGGED: CAUTION**")
    st.write("Projected cash is dropping significantly. Monitor expenses closely.")
    risk_level = "CAUTION"
else:
    st.success("🟢 **RISK CONDITION: HEALTHY**")
    st.write("Cash position is projected to remain stable and positive.")
    risk_level = "HEALTHY"

# Generate Recommendations based on risk
st.markdown("#### 🤖 Agent Recommendations")
if risk_level == "AT RISK":
    st.write("1. **Reduce Expenses**: Identify and cut non-essential costs immediately.")
    st.write("2. **Increase Income**: Launch promotions or chase outstanding invoices.")
    st.write("3. **Secure Funding**: Consider a short-term loan or overdraft facility.")
elif risk_level == "CAUTION":
    st.write("1. **Monitor Closely**: Review weekly cash flow reports.")
    st.write("2. **Delay Big Purchases**: Postpone large capital expenses.")
    st.write("3. **Negotiate Terms**: Ask suppliers for extended payment terms.")
else:
    st.write("1. **Reinvest**: Consider investing surplus cash for growth.")
    st.write("2. **Build Reserve**: Set aside 3-6 months of expenses as an emergency fund.")
    st.write("3. **Plan Expansion**: You have room to scale operations or marketing.")
