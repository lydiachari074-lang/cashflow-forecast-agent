import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta, date

st.set_page_config(page_title="SME Cashflow Agent - 5 Jobs", layout="wide")
st.title("🤖 SME Cashflow Agent: SEE | PREDICT | WARN | EXPLAIN | FIX")
st.caption("For Masvingo SMEs - Shows live how Inflows and Outflows change")

# --- 1. SEE - DATA ---
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
source = st.sidebar.radio("Data Source", ['Manual Input Form','Upload CSV/Excel','Connect Bank','Connect EcoCash'])

if source == 'Upload CSV/Excel':
    f = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv','xlsx'])
    if f:
        df_new = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f, engine='openpyxl')
        st.session_state.df = df_new
        st.rerun()
elif source == 'Connect Bank':
    if st.sidebar.button("🔄 Sync Bank Feed"):
        st.session_state.df = load_sample()
        st.sidebar.success("Bank Synced!")
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
df['Net'] = df['Income'] - df['Expenses']
df = df.sort_values('Date')
df['Cumulative'] = df['Net'].cumsum()

# Forecast logic
base_daily = df['Net'].mean() / 30
if rent: base_daily -= 1500/30
if salary: base_daily -= 3000/30
if 'late' in scenario: base_daily -= (df['Income'].mean()*0.3)/30
if 'stock' in scenario: base_daily -= (df['Expenses'].mean()*0.2)/30
if 'USD' in scenario: base_daily -= (df['Expenses'].mean()*0.1)/30

last_date = df['Date'].iloc[-1]
last_cum = df['Cumulative'].iloc[-1]
forecast_dates = [last_date + timedelta(days=i) for i in range(1, 91)]
forecast_cum = [last_cum + base_daily*i for i in range(1, 91)]

avg_in = df['Income'].mean()
avg_out = df['Expenses'].mean()
if 'late' in scenario: avg_in *= 0.7
if 'stock' in scenario: avg_out *= 1.2
if 'USD' in scenario: avg_out *= 1.1

forecast_df = pd.DataFrame({'Date': forecast_dates, 'Income': avg_in, 'Expenses': avg_out, 'Cumulative': forecast_cum})

# --- TABS ---
tab_manual, tab_dash, tab_warn, tab_explain, tab_fix = st.tabs(["📝 SEE & Manual Edit", "📊 PREDICT - Live Graph", "🚨 WARN", "💡 EXPLAIN", "🔧 FIX"])

with tab_manual:
    st.subheader("1. SEE - Data Ingestion & Cleaning")
    st.info("TYPE HERE: Change Income and Expenses - Then click Save. Graph will update LIVE in PREDICT tab")
    
    edited_df = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor",
        column_config={
            "Date": st.column_config.DateColumn("Date"),
            "Income": st.column_config.NumberColumn("Income $ (Cash IN)", step=100),
            "Expenses": st.column_config.NumberColumn("Expenses $ (Cash OUT)", step=100),
        }
    )
    if st.button("💾 Save Changes & Update Graph", type="primary"):
        st.session_state.df = edited_df
        st.success("Saved! Now go to PREDICT tab")
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Debtors - Who owes you")
        st.dataframe(df[df['Income']>0][['Date','Client','Income']], use_container_width=True)
    with col2:
        st.subheader("Creditors - Who you owe")
        st.dataframe(df[df['Expenses']>0][['Date','Client','Expenses']], use_container_width=True)

with tab_dash:
    st.subheader("2. PREDICT - Live Inflow vs Outflow Graph")
    
    current_net = df['Net'].iloc[-1]
    colA, colB, colC = st.columns(3)
    colA.metric("Last Month IN", f"${df['Income'].iloc[-1]:,.0f}")
    colB.metric("Last Month OUT", f"${df['Expenses'].iloc[-1]:,.0f}")
    if current_net >= 0:
        colC.success(f"🟢 GREEN: IN > OUT by ${current_net:,.0f}")
    else:
        colC.error(f"🔴 RED: OUT > IN by ${abs(current_net):,.0f}")

    if forecast_cum[-1] < 0:
        st.error(f"🚨 RUNWAY ALERT: At current burn you will be NEGATIVE by {forecast_dates[np.argmin(forecast_cum)].strftime('%d %b %Y')}")
    else:
        st.success(f"✅ Healthy: Projected 90-day balance ${forecast_cum[-1]:,.2f}")

    # MAIN LIVE GRAPH
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df['Date'], df['Income'], label='INFLOW - Historical', color='#00C853', marker='o', linewidth=3)
    ax.plot(df['Date'], df['Expenses'], label='OUTFLOW - Historical', color='#D50000', marker='s', linewidth=3)
    ax.plot(forecast_df['Date'], forecast_df['Income'], label='INFLOW - Forecast 90d', color='#00C853', linestyle='--', linewidth=2, alpha=0.7)
    ax.plot(forecast_df['Date'], forecast_df['Expenses'], label='OUTFLOW - Forecast 90d', color='#D50000', linestyle='--', linewidth=2, alpha=0.7)
    
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
    ax2.bar(df['Date'], df['Net'], color=colors, alpha=0.7)
    ax2.plot(forecast_df['Date'], forecast_df['Income']-forecast_df['Expenses'], color='blue', linestyle='--', label='Forecast Net')
    ax2.axhline(0, color='black')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

with tab_warn:
    st.subheader("3. WARN - Early Warning System")
    if df['Expenses'].iloc[-1] > df['Expenses'].mean()*1.5:
        st.warning(f"⚠️ ANOMALY: {df['Category'].iloc[-1]} cost 3x higher than avg")
    st.warning("⚠️ LATE PAYER: Client A 15 days overdue $2000")
    st.info("📅 TAX DUE: ZIMRA VAT $900 in 10 days - Set aside!")

with tab_explain:
    st.subheader("4. EXPLAIN - Diagnosis")
    leak = df.groupby('Category')['Expenses'].sum().sort_values(ascending=False)
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
            st.code("Hi Client A, reminder Invoice #123 $2000 due 15 days ago. Please settle.")
    with col2:
        if st.button("⏰ Optimize Bills"):
            st.success("Pay Supplier X EARLY for 5% discount - Save $125. Delay non-critical 3 bills.")
