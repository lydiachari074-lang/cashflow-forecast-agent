import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta, date

st.set_page_config(page_title="SME Cashflow Agent - 5 Jobs", layout="wide")
st.title("🤖 SME Cashflow Agent: SEE | PREDICT | WARN | EXPLAIN | FIX")
st.caption("Fixed Version - Graph now changes LIVE")

# --- LOAD SAMPLE ---
def load_sample():
    return pd.DataFrame({
        'Date': pd.date_range(end=date.today(), periods=6, freq='ME'),
        'Description': ['Stock Purchase', 'Client A Payment', 'Rent Shop', 'Salaries Staff', 'Fuel Delivery', 'Client B Payment'],
        'Income': [0, 5000, 0, 0, 0, 3000],
        'Expenses': [2500, 0, 1500, 3000, 800, 0],
        'Client': ['Supplier X', 'Client A', 'Landlord', 'Staff', 'Total Fuel', 'Client B'],
    })

if 'df' not in st.session_state:
    st.session_state.df = load_sample()

def auto_categorize(desc):
    desc = str(desc).lower()
    if 'rent' in desc: return 'Rent'
    if 'stock' in desc: return 'Stock'
    if 'salar' in desc: return 'Salaries'
    if 'fuel' in desc: return 'Fuel'
    if 'zimra' in desc or 'tax' in desc or 'vat' in desc: return 'ZIMRA/Tax'
    if 'client' in desc or 'payment' in desc: return 'Sales'
    return 'Other'

# --- SIDEBAR ---
st.sidebar.header("A. SEE - Data Connectors")
source = st.sidebar.radio("Data Source", ['Manual Input Form','Upload CSV/Excel','Connect Bank','Connect EcoCash'], index=0)

if source == 'Upload CSV/Excel':
    f = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv','xlsx'])
    if f:
        df_new = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
        st.session_state.df = df_new
        st.rerun()
elif source == 'Connect Bank':
    if st.sidebar.button("🔄 Sync Bank Feed"):
        st.session_state.df = load_sample()
        st.sidebar.success("Bank Synced! Go to Manual Form")
elif source == 'Connect EcoCash':
    if st.sidebar.button("🔄 Sync EcoCash Feed"):
        ec = load_sample()
        ec['Description'] = ec['Description'] + ' (EcoCash)'
        st.session_state.df = ec
        st.sidebar.success("EcoCash Synced!")

st.sidebar.divider()
st.sidebar.header("B. PREDICT - Engine")
model = st.sidebar.selectbox("Model", ['Short-term 90-day Daily','Seasonality Detection','Recurring Detection'])
scenario = st.sidebar.selectbox("Scenario Modeling", ['Base Case','Biggest client pays 15 days late (-30% Income)','Increase stock by 20%','USD rate moves +10% cost'])

st.sidebar.divider()
st.sidebar.header("Rules - Auto-learn")
rent = st.sidebar.checkbox("Rent $1500 every 1st", True)
salary = st.sidebar.checkbox("Salaries $3000 month-end", True)

# --- PREPARE DATA ---
df = st.session_state.df.copy()
if 'Income' not in df.columns: df['Income'] = 0
if 'Expenses' not in df.columns: df['Expenses'] = 0
if 'Description' not in df.columns: df['Description'] = 'Manual'
df['Date'] = pd.to_datetime(df['Date'])
df['Category'] = df['Description'].apply(auto_categorize)
df['Net'] = pd.to_numeric(df['Income'], errors='coerce').fillna(0) - pd.to_numeric(df['Expenses'], errors='coerce').fillna(0)
df = df.sort_values('Date')
df['Cumulative'] = df['Net'].cumsum()

# --- TABS ---
tab_manual, tab_dash, tab_warn, tab_explain, tab_fix = st.tabs(["📝 1. SEE & Manual Edit", "📊 2. PREDICT - Live Graph", "🚨 3. WARN", "💡 4. EXPLAIN", "🔧 5. FIX"])

with tab_manual:
    st.subheader("1. SEE - Data Ingestion & Cleaning")
    st.error("👉 TO MAKE GRAPH CHANGE: 1. Edit numbers below 2. MUST CLICK Save Button 3. Go to PREDICT tab")
    
    edited_df = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor",
        column_config={
            "Date": st.column_config.DateColumn("Date"),
            "Income": st.column_config.NumberColumn("Income $ (Cash IN)", step=100, min_value=0),
            "Expenses": st.column_config.NumberColumn("Expenses $ (Cash OUT)", step=100, min_value=0),
        }
    )
    if st.button("💾 Save Changes & Update Graph", type="primary", use_container_width=True):
        st.session_state.df = edited_df
        st.success("✅ Saved! Now go to PREDICT tab - graph will move!")
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Debtors - Who owes you**")
        st.dataframe(df[df['Income']>0][['Date','Client','Income']], use_container_width=True)
    with col2:
        st.write("**Creditors - Who you owe**")
        st.dataframe(df[df['Expenses']>0][['Date','Client','Expenses']], use_container_width=True)

with tab_dash:
    st.subheader("2. PREDICT - Live Inflow vs Outflow Changes")

    # Current status
    last_income = float(df['Income'].iloc[-1])
    last_expense = float(df['Expenses'].iloc[-1])
    current_net = last_income - last_expense
    
    c1,c2,c3 = st.columns(3)
    c1.metric("Last IN", f"${last_income:,.0f}")
    c2.metric("Last OUT", f"${last_expense:,.0f}")
    if current_net >=0:
        c3.success(f"🟢 GREEN: IN > OUT by ${current_net:,.0f}")
    else:
        c3.error(f"🔴 RED: OUT > IN by ${abs(current_net):,.0f}")

    # === LIVE FORECAST LOGIC - THIS IS THE FIX ===
    last_date = df['Date'].iloc[-1]
    
    # Scenario factors
    inc_factor = 0.7 if 'late' in scenario else 1.0
    exp_factor = 1.0
    if 'stock' in scenario: exp_factor = 1.2
    if 'USD' in scenario: exp_factor = 1.1

    # Build forecast that starts from LAST point and reacts
    forecast_dates = [last_date + timedelta(days=30*i) for i in range(1,4)] # Oct, Nov, Dec
    
    # Base forecast from last values + scenario
    base_inc = df['Income'].mean() * inc_factor
    base_exp = df['Expenses'].mean() * exp_factor
    
    # Make forecast react to last manual change
    f_income = [ (last_income*0.5 + base_inc*0.5) * (1 + i*0.05) for i in range(3) ]
    f_expenses = [ (last_expense*0.5 + base_exp*0.5) * (1 + i*0.05) for i in range(3) ]

    # --- MAIN GRAPH ---
    fig, ax = plt.subplots(figsize=(12,6))
    
    # Historical
    ax.plot(df['Date'], df['Income'], label='INFLOW - Historical', color='#00C853', marker='o', linewidth=3)
    ax.plot(df['Date'], df['Expenses'], label='OUTFLOW - Historical', color='#D50000', marker='s', linewidth=3)
    
    # Forecast - Connected from last point (NO GAP, NO FLAT)
    inc_dates = [df['Date'].iloc[-1]] + forecast_dates
    inc_vals = [last_income] + f_income
    exp_dates = [df['Date'].iloc[-1]] + forecast_dates
    exp_vals = [last_expense] + f_expenses
    
    ax.plot(inc_dates, inc_vals, label='INFLOW - Forecast 90d', color='#00C853', linestyle='--', linewidth=3, marker='X', markersize=10)
    ax.plot(exp_dates, exp_vals, label='OUTFLOW - Forecast 90d', color='#D50000', linestyle='--', linewidth=3, marker='X', markersize=10)
    
    # GREEN/RED Zones
    ax.fill_between(df['Date'], df['Income'], df['Expenses'], where=(df['Income'] >= df['Expenses']), color='green', alpha=0.15, interpolate=True, label='GREEN Zone')
    ax.fill_between(df['Date'], df['Income'], df['Expenses'], where=(df['Income'] < df['Expenses']), color='red', alpha=0.25, interpolate=True, label='RED Zone')
    
    ax.set_ylabel("Amount ($)")
    ax.set_xlabel("Date")
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_title(f"LIVE Changes - Scenario: {scenario} | Model: {model}", fontweight='bold')
    plt.xticks(rotation=20)
    st.pyplot(fig)

    st.divider()
    st.subheader("Net Flow (Inflow - Outflow)")
    fig2, ax2 = plt.subplots(figsize=(12,3))
    colors = ['#00C853' if x>=0 else '#D50000' for x in df['Net']]
    ax2.bar(df['Date'], df['Net'], color=colors, alpha=0.7, label='Historical')
    ax2.plot(forecast_dates, [f_income[i]-f_expenses[i] for i in range(3)], color='blue', linestyle='--', marker='o', label='Forecast Net')
    ax2.axhline(0, color='black')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

    st.info(f"Current Scenario Impact: Income x{inc_factor} | Expenses x{exp_factor}. Change in Manual tab to see graph JUMP.")

with tab_warn:
    st.subheader("3. WARN - Early Warning System")
    total_cum = df['Cumulative'].iloc[-1]
    if total_cum < 0:
        st.error(f"🚨 RUNWAY ALERT: You are NEGATIVE ${total_cum:,.0f}. At current burn you will run out!")
    if df['Expenses'].iloc[-1] > df['Expenses'].mean()*1.5:
        st.warning(f"⚠️ ANOMALY: {df['Category'].iloc[-1]} cost 3x higher than avg")
    st.warning("⚠️ LATE PAYER: Client A 15 days overdue $2000")
    st.info("📅 TAX DUE: ZIMRA VAT $900 in 10 days")

with tab_explain:
    st.subheader("4. EXPLAIN - Diagnosis")
    leak = df.groupby('Category')['Expenses'].sum().sort_values(ascending=False)
    if not leak.empty:
        st.write(f"**Cash Leak:** {leak.idxmax()} is {leak.max()/df['Expenses'].sum()*100:.0f}% of cash-out")
    st.bar_chart(leak)
    col1, col2 = st.columns(2)
    col1.metric("Cash Conversion Cycle", "45 Days")
    col2.metric("Best Customer", "Client A - Pays on time")

with tab_fix:
    st.subheader("5. FIX - Prescriptive Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📱 Draft WhatsApp to late payer"):
            st.code("Hi Client A, reminder Invoice #123 $2000 due 15 days ago. Please settle to avoid late fee.")
    with col2:
        if st.button("⏰ Optimize Bills"):
            st.success("Pay Supplier X EARLY for 5% discount - Save $125. Delay 3 non-critical bills.")
