import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Bank Statement Analyzer", page_icon="🏦", layout="wide")

st.markdown("# 🏦 Bank Statement Analyzer")
st.markdown("### Demo Dashboard - Heron-style Analysis")

# Generate sample data
@st.cache_data
def get_demo_data():
              dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
              data = []
              balance = 45000

    categories = ['Revenue', 'MCA Payment', 'Loan Payment', 'Payroll', 'Rent', 'Utilities', 'Supplies', 'Bank Fee']

    for date in dates:
                      n_trans = random.randint(1, 5)
                      for _ in range(n_trans):
                                            cat = random.choice(categories)
                                            if cat == 'Revenue':
                                                                      amt = round(random.uniform(500, 15000), 2)
elif cat in ['MCA Payment', 'Loan Payment']:
                amt = -round(random.uniform(200, 2000), 2)
elif cat == 'Payroll':
                amt = -round(random.uniform(2000, 8000), 2)
elif cat == 'Rent':
                amt = -round(random.uniform(2000, 5000), 2)
else:
                amt = -round(random.uniform(50, 500), 2)

                      balance += amt
            data.append({'Date': date, 'Category': cat, 'Amount': amt, 'Balance': round(balance, 2)})

    return pd.DataFrame(data)

df = get_demo_data()

# Sidebar
st.sidebar.title("📊 Quick Stats")
st.sidebar.metric("Total Transactions", len(df))
total_rev = df[df['Amount'] > 0]['Amount'].sum()
total_exp = abs(df[df['Amount'] < 0]['Amount'].sum())
st.sidebar.metric("Total Revenue", f"${total_rev:,.2f}")
st.sidebar.metric("Total Expenses", f"${total_exp:,.2f}")
st.sidebar.metric("Current Balance", f"${df['Balance'].iloc[-1]:,.2f}")

# Main metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
              st.metric("Revenue (90 days)", f"${total_rev:,.2f}")
with col2:
              mca = abs(df[df['Category'] == 'MCA Payment']['Amount'].sum())
    st.metric("MCA Payments", f"${mca:,.2f}")
with col3:
              loans = abs(df[df['Category'] == 'Loan Payment']['Amount'].sum())
    st.metric("Loan Payments", f"${loans:,.2f}")
with col4:
              st.metric("Avg Balance", f"${df['Balance'].mean():,.2f}")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Transactions", "📈 Balance Trend", "🎯 Scorecard", "💳 Debt Analysis"])

with tab1:
              st.subheader("Transaction History")
    cat_filter = st.multiselect("Filter by Category", df['Category'].unique())
    if cat_filter:
                      st.dataframe(df[df['Category'].isin(cat_filter)], use_container_width=True)
else:
        st.dataframe(df, use_container_width=True)

with tab2:
              st.subheader("Daily Balance Trend")
    daily = df.groupby('Date')['Balance'].last().reset_index()
    st.line_chart(daily.set_index('Date'))

with tab3:
              st.subheader("Risk Scorecard")
    score = 75
    st.markdown(f"## Overall Score: {'🟢' if score >= 70 else '🟡' if score >= 50 else '🔴'} {score}/100")
    scores = pd.DataFrame({'Metric': ['Revenue Health', 'Debt Burden', 'Cash Flow', 'NSF/Overdraft'], 'Score': [80, 70, 75, 85], 'Weight': ['30%', '25%', '25%', '20%']})
    st.dataframe(scores, use_container_width=True)

with tab4:
              st.subheader("Debt Analysis")
    mca_df = df[df['Category'] == 'MCA Payment']
    if len(mca_df) > 0:
                      st.warning(f"⚠️ {len(mca_df)} MCA payments detected totaling ${abs(mca_df['Amount'].sum()):,.2f}")
                      st.dataframe(mca_df[['Date', 'Amount']], use_container_width=True)
                  loan_df = df[df['Category'] == 'Loan Payment']
    if len(loan_df) > 0:
                      st.info(f"📊 {len(loan_df)} loan payments totaling ${abs(loan_df['Amount'].sum()):,.2f}")

st.sidebar.markdown("---")
st.sidebar.info("📁 Upload a PDF bank statement to analyze real data")
