import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime

st.set_page_config(page_title="Bank Statement Analyzer", page_icon="🏦", layout="wide")

# Merchant patterns for categorization
MERCHANTS = {'STRIPE': ('Revenue', 'revenue'), 'SQUARE': ('Revenue', 'revenue'), 'SHOPIFY': ('Revenue', 'revenue'), 'PAYPAL': ('Revenue', 'revenue'), 'ACH CREDIT': ('Revenue', 'revenue'), 'DAILY ACH': ('MCA Payment', 'mca'), 'MCA': ('MCA Payment', 'mca'), 'MERCHANT CASH': ('MCA Payment', 'mca'), 'SBA LOAN': ('Loan Payment', 'loan'), 'LOAN PMT': ('Loan Payment', 'loan'), 'ADP PAYROLL': ('Payroll', 'op'), 'GUSTO': ('Payroll', 'op'), 'PAYROLL': ('Payroll', 'op'), 'RENT': ('Rent', 'op'), 'NSF': ('NSF Fee', 'fee'), 'OVERDRAFT': ('Overdraft', 'fee')}

if 'learned' not in st.session_state:
              st.session_state.learned = {}

def categorize(desc):
              d = desc.upper()
              for k, v in {**MERCHANTS, **st.session_state.learned}.items():
                                if k in d:
                                                      return v
                                              return ('Other', 'other')

          # Sidebar with PDF upload
          st.sidebar.title("🏦 Bank Statement Analyzer")
uploaded = st.sidebar.file_uploader("📄 Upload PDF", type=['pdf'])
demo = st.sidebar.checkbox("Use Demo Data", value=True)

# Generate or parse data
if demo:
              np.random.seed(42)
              n = 200
              descs = ['STRIPE TRANSFER', 'SQUARE INC', 'DAILY ACH DEBIT', 'MCA PAYMENT', 'SBA LOAN PMT', 'ADP PAYROLL', 'RENT PAYMENT', 'NSF FEE', 'SHOPIFY PAYOUT']
              df = pd.DataFrame({'Date': pd.date_range(end='2026-02-05', periods=n), 'Description': np.random.choice(descs, n), 'Amount': np.random.uniform(-5000, 10000, n).round(2)})
else:
              if uploaded:
                                try:
                                                      import pdfplumber
                                                      with pdfplumber.open(uploaded) as pdf:
                                                                                text = ''.join([p.extract_text() or '' for p in pdf.pages])
                                                                            lines = [l for l in text.split('\n') if re.search(r'\d+\.\d{2}', l)]
                                                      data = []
                                                      for l in lines[:100]:
                                                                                amts = re.findall(r'[\d,]+\.\d{2}', l)
                                                                                if amts:
                                                                                                              data.append({'Date': datetime.now(), 'Description': l[:50], 'Amount': float(amts[-1].replace(',', ''))})
                                                                                                      df = pd.DataFrame(data) if data else None
                                                                            if df is None:
                                                                                                      st.sidebar.warning("Could not parse PDF")
                                                                                                      demo = True
                                                                                              except:
                                                      st.sidebar.error("PDF parsing failed")
                                    demo = True
    if demo or 'df' not in dir() or df is None:
                      np.random.seed(42)
        n = 200
        descs = ['STRIPE TRANSFER', 'SQUARE INC', 'DAILY ACH DEBIT', 'MCA PAYMENT', 'SBA LOAN PMT', 'ADP PAYROLL', 'RENT PAYMENT', 'NSF FEE']
        df = pd.DataFrame({'Date': pd.date_range(end='2026-02-05', periods=n), 'Description': np.random.choice(descs, n), 'Amount': np.random.uniform(-5000, 10000, n).round(2)})

# Categorize
cats = df['Description'].apply(categorize)
df['Category'] = [c[0] for c in cats]
df['Type'] = [c[1] for c in cats]
df['Balance'] = 45000 + df['Amount'].cumsum()

# Metrics
rev = df[df['Type'] == 'revenue']['Amount'].sum()
mca = abs(df[df['Type'] == 'mca']['Amount'].sum())
loans = abs(df[df['Type'] == 'loan']['Amount'].sum())
fees = len(df[df['Type'] == 'fee'])

# Scoring
score_rev = 90 if rev > 100000 else 70 if rev > 50000 else 50
score_debt = 90 if (mca + loans) / max(rev, 1) < 0.15 else 60 if (mca + loans) / max(rev, 1) < 0.3 else 30
score_cash = 90 if df['Balance'].mean() > 50000 else 70 if df['Balance'].mean() > 20000 else 40
score_nsf = 100 if fees == 0 else 60 if fees < 3 else 20
score = int(score_rev * 0.3 + score_debt * 0.25 + score_cash * 0.25 + score_nsf * 0.2)

st.sidebar.metric("Score", f"{score}/100")
st.sidebar.metric("Revenue", f"${rev:,.0f}")

# Main
st.title("🏦 Bank Statement Analyzer")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${rev:,.0f}")
c2.metric("MCA Debt", f"${mca:,.0f}")
c3.metric("Loan Pmts", f"${loans:,.0f}")
c4.metric("Avg Bal", f"${df['Balance'].mean():,.0f}")

st.divider()
t1, t2, t3, t4, t5 = st.tabs(["📋 Transactions", "📈 Balance", "🎯 Scorecard", "💳 Debt", "🧠 Learning"])

with t1:
              st.dataframe(df[['Date', 'Description', 'Category', 'Amount', 'Balance']], use_container_width=True)

with t2:
              st.line_chart(df.set_index('Date')['Balance'])

with t3:
              color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
    st.markdown(f"## {color} {score}/100")
    st.dataframe(pd.DataFrame({'Factor': ['Revenue', 'Debt', 'Cash', 'NSF'], 'Score': [score_rev, score_debt, score_cash, score_nsf], 'Weight': ['30%', '25%', '25%', '20%']}))

with t4:
              mca_df = df[df['Type'] == 'mca']
    if len(mca_df) > 0:
                      st.error(f"⚠️ {len(mca_df)} MCA payments: ${abs(mca_df['Amount'].sum()):,.0f}")
        st.dataframe(mca_df[['Date', 'Description', 'Amount']])
    loan_df = df[df['Type'] == 'loan']
    if len(loan_df) > 0:
                      st.info(f"📊 {len(loan_df)} loan payments: ${abs(loan_df['Amount'].sum()):,.0f}")

with t5:
              st.subheader("🧠 Train New Patterns")
    other_df = df[df['Category'] == 'Other'][['Description']].drop_duplicates()
    if len(other_df) > 0:
                      st.warning(f"{len(other_df)} unrecognized merchants")
        desc = st.selectbox("Select merchant", other_df['Description'].tolist())
        cat = st.selectbox("Category", ['Revenue', 'MCA Payment', 'Loan Payment', 'Payroll', 'Rent', 'Other'])
        if st.button("Learn"):
                              typ = {'Revenue': 'revenue', 'MCA Payment': 'mca', 'Loan Payment': 'loan'}.get(cat, 'op')
            key = desc.upper().split()[0] if desc else 'UNKNOWN'
            st.session_state.learned[key] = (cat, typ)
            st.success(f"Learned: {key} = {cat}")
    st.markdown(f"**Learned:** {len(st.session_state.learned)} patterns")
