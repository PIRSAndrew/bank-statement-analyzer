import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Bank Statement Analyzer", page_icon="🏦", layout="wide")

st.title("🏦 Bank Statement Analyzer")
st.subheader("Demo Dashboard - Heron-style Analysis")

# Create sample data directly
np.random.seed(42)
n = 200
df = pd.DataFrame({
      'Date': pd.date_range(end='2026-02-05', periods=n),
      'Category': np.random.choice(['Revenue', 'MCA Payment', 'Loan Payment', 'Payroll', 'Rent', 'Utilities'], n),
      'Amount': np.random.uniform(-5000, 10000, n).round(2)
})
df['Balance'] = 45000 + df['Amount'].cumsum()

# Sidebar stats
st.sidebar.title("📊 Quick Stats")
st.sidebar.metric("Transactions", len(df))
rev = df[df['Amount'] > 0]['Amount'].sum()
exp = abs(df[df['Amount'] < 0]['Amount'].sum())
st.sidebar.metric("Total Revenue", f"${rev:,.0f}")
st.sidebar.metric("Total Expenses", f"${exp:,.0f}")

# Main metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${rev:,.0f}")
c2.metric("MCA Payments", f"${abs(df[df['Category']=='MCA Payment']['Amount'].sum()):,.0f}")
c3.metric("Loan Payments", f"${abs(df[df['Category']=='Loan Payment']['Amount'].sum()):,.0f}")
c4.metric("Avg Balance", f"${df['Balance'].mean():,.0f}")

st.divider()

# Tabs
t1, t2, t3, t4 = st.tabs(["📋 Transactions", "📈 Balance", "🎯 Scorecard", "💳 Debt"])

with t1:
      st.subheader("Transaction History")
      st.dataframe(df, use_container_width=True)

with t2:
      st.subheader("Balance Trend")
      st.line_chart(df.set_index('Date')['Balance'])

with t3:
      st.subheader("Risk Scorecard")
      st.markdown("## 🟢 75/100")
      st.dataframe(pd.DataFrame({'Metric': ['Revenue', 'Debt', 'Cash Flow', 'NSF'], 'Score': [80, 70, 75, 85]}))

with t4:
      st.subheader("Debt Analysis")
      mca = df[df['Category']=='MCA Payment']
      st.warning(f"⚠️ {len(mca)} MCA payments: ${abs(mca['Amount'].sum()):,.0f}")
      st.dataframe(mca)
