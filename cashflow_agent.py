# --- STEP 3: ASSESS FINANCIAL RISK & GENERATE RECOMMENDATIONS ---
st.markdown("### ⚠️ Step 3: Assess Financial Risk & Recommendations")

# Get last forecasted cumulative cash
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

st.markdown("---"). Is this code usefull
