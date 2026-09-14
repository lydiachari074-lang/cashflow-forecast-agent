import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas # For PDF Report

st.set_page_config(page_title="AI Cash Flow Agent", layout="wide")
st.title("🤖 AI Cash Flow Forecasting Dashboard Agent")

# --- SIDEBAR ---
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV: Date, Income, Expenses", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv("sample_data.csv") 

df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')
df['Net Cash Flow'] = df['Income'] - df['Expenses']
df['Cumulative Cash'] = df['Net Cash Flow'].cumsum()

# --- FORECAST LOGIC ---
avg_net_cash = df['Net Cash Flow'].mean()
last_date = df['Date'].iloc[-1]
last_cumulative = df['Cumulative Cash'].iloc[-1]
forecast_dates = [last_date + timedelta(days=30*i) for i in range(1, 4)]
forecast_cumulative = [last_cumulative + avg_net_cash*i for i in range(1, 4)]
forecast_df = pd.DataFrame({'Date': forecast_dates, 'Cumulative Cash': forecast_cumulative})

# --- D. OUTPUT + ACTION LAYER ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 1. Dashboard", "🚨 2. Alerts", "📄 3. Report Generator", "⚡ 4. Action Tools"])

# 1. DASHBOARD / VISUALIZATION
with tab1:
    st.header("Dashboard / Visualization")
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
    ax1.legend()
    ax1.grid(True)
    st.pyplot(fig1)

# 2. ALERTS
with tab2:
    st.header("🚨 AI Alerts")
    for i, row in forecast_df.iterrows():
        if row['Cumulative Cash'] < 0:
            date_str = row['Date'].strftime('%b %d')
            st.error(f"Warning: You will be ${abs(row['Cumulative Cash']):,.0f} short on {date_str}")
        elif row['Cumulative Cash'] < last_cumulative * 0.5:
            date_str = row['Date'].strftime('%b %d')
            st.warning(f"Caution: Cash will drop below 50% by {date_str}")
    
    if forecast_cumulative[-1] > last_cumulative:
        st.success("✅ Healthy: Projected cash is increasing over next 90 days")

# 3. REPORT GENERATOR
with tab3:
    st.header("📄 Weekly Cashflow Forecast Report")
    
    def create_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer)
        c.drawString(100, 800, "AI Cash Flow Forecast Report")
        c.drawString(100, 780, f"Generated: {datetime.now().strftime('%Y-%m-%d')}")
        c.drawString(100, 760, f"Current Balance: ${last_cumulative:,.2f}")
        c.drawString(100, 740, f"Projected Balance in 90 Days: ${forecast_cumulative[-1]:,.2f}")
        c.drawString(100, 720, "--- Forecast ---")
        y = 700
        for i, row in forecast_df.iterrows():
            c.drawString(100, y, f"{row['Date'].strftime('%Y-%m-%d')}: ${row['Cumulative Cash']:,.2f}")
            y -= 20
        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf()
    st.download_button(
        label="📥 Download Forecast PDF",
        data=pdf_buffer,
        file_name="cashflow_report.pdf",
        mime="application/pdf"
    )
    st.info("Tip: You can also export the data table to CSV and upload to Google Sheets")
    st.dataframe(pd.concat([df[['Date','Income','Expenses','Cumulative Cash']], forecast_df]), use_container_width=True)

# 4. ACTION TOOLS
with tab4:
    st.header("⚡ AI Action Tools")
    st.markdown("Based on your forecast, here are recommended actions:")
    
    if forecast_cumulative[-1] < last_cumulative:
        st.button("✉️ Email Client to Pay Invoice", on_click=lambda: st.success("Email template copied! 'Dear Client, Kindly settle invoice to improve cashflow.'"))
        st.button("⏰ Suggest Delaying This Expense", on_click=lambda: st.success("Action: Flag non-critical expenses for next 30 days"))
    
    st.button("💰 Suggest Ways to Increase Income", on_click=lambda: st.info("1. Run a promotion 2. Follow up on receivables 3. Offer discounts for upfront payment"))
    st.button("📉 Suggest Ways to Cut Costs", on_click=lambda: st.info("1. Negotiate with suppliers 2. Delay equipment purchase 3. Review subscriptions"))
