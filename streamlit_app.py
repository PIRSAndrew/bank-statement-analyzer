import streamlit as st
import pandas as pd
import numpy as np
import re
import json
from datetime import datetime

st.set_page_config(page_title="Bank Statement Analyzer", page_icon="🏦", layout="wide")

# Initialize session state for learned merchants
if 'merchant_db' not in st.session_state:
          st.session_state.merchant_db = {
                        'STRIPE': {'category': 'Revenue', 'type': 'revenue', 'confidence': 0.95},
                        'SQUARE': {'category': 'Revenue', 'type': 'revenue', 'confidence': 0.95},
                        'SHOPIFY': {'category': 'Revenue', 'type': 'revenue', 'confidence': 0.95},
                        'PAYPAL': {'category': 'Revenue', 'type': 'revenue', 'confidence': 0.90},
                        'ACH CREDIT': {'category': 'Revenue', 'type': 'revenue', 'confidence': 0.85},
                        'WIRE IN': {'category': 'Revenue', 'type': 'revenue', 'confidence': 0.85},
                        'DAILY ACH': {'category': 'MCA Payment', 'type': 'mca_debt', 'confidence': 0.90},
                        'MCA': {'category': 'MCA Payment', 'type': 'mca_debt', 'confidence': 0.95},
                        'MERCHANT CASH': {'category': 'MCA Payment', 'type': 'mca_debt', 'confidence': 0.95},
                        'RAPID ADVANCE': {'category': 'MCA Payment', 'type': 'mca_debt', 'confidence': 0.90},
                        'BUSINESS FUNDING': {'category': 'MCA Payment', 'type': 'mca_debt', 'confidence': 0.85},
                        'SBA LOAN': {'category': 'Loan Payment', 'type': 'loan', 'confidence': 0.95},
                        'LOAN PMT': {'category': 'Loan Payment', 'type': 'loan', 'confidence': 0.90},
                        'LINE OF CREDIT': {'category': 'LOC Payment', 'type': 'loan', 'confidence': 0.90},
                        'EQUIPMENT LEASE': {'category': 'Lease Payment', 'type': 'loan', 'confidence': 0.90},
                        'ADP PAYROLL': {'category': 'Payroll', 'type': 'operating', 'confidence': 0.95},
                        'GUSTO': {'category': 'Payroll', 'type': 'operating', 'confidence': 0.95},
                        'PAYROLL': {'category': 'Payroll', 'type': 'operating', 'confidence': 0.90},
                        'RENT': {'category': 'Rent', 'type': 'operating', 'confidence': 0.85},
                        'LEASE': {'category': 'Rent', 'type': 'operating', 'confidence': 0.80},
                        'INSURANCE': {'category': 'Insurance', 'type': 'operating', 'confidence': 0.85},
                        'UTILITY': {'category': 'Utilities', 'type': 'operating', 'confidence': 0.85},
                        'ELECTRIC': {'category': 'Utilities', 'type': 'operating', 'confidence': 0.85},
                        'NSF': {'category': 'NSF Fee', 'type': 'fee', 'confidence': 0.95},
                        'OVERDRAFT': {'category': 'Overdraft Fee', 'type': 'fee', 'confidence': 0.95},
                        'BANK FEE': {'category': 'Bank Fee', 'type': 'fee', 'confidence': 0.90},
          }

if 'learned_patterns' not in st.session_state:
          st.session_state.learned_patterns = []

def categorize_transaction(desc, amount):
          desc_upper = desc.upper()
          best_match = None
          best_conf = 0
          for pattern, info in st.session_state.merchant_db.items():
                        if pattern in desc_upper:
                                          if info['confidence'] > best_conf:
                                                                best_conf = info['confidence']
                                                                best_match = info
                                                    if best_match:
                                                                  return best_match['category'], best_match['type'], best_conf
                                                              if amount > 0:
                                                                            return 'Other Income', 'other_income', 0.5
                                                                        return 'Other Expense', 'other_expense', 0.5

                def learn_merchant(desc, category, tx_type):
                          words = desc.upper().split()
                          if len(words) >= 2:
                                        pattern = ' '.join(words[:2])
else:
        pattern = words[0] if words else desc.upper()
    st.session_state.merchant_db[pattern] = {'category': category, 'type': tx_type, 'confidence': 0.80}
    st.session_state.learned_patterns.append({'pattern': pattern, 'category': category, 'learned_at': datetime.now().isoformat()})

def parse_pdf_text(text):
          lines = text.split('\n')
    transactions = []
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    amount_pattern = r'[\$]?([\d,]+\.\d{2})'
    for line in lines:
                  dates = re.findall(date_pattern, line)
                  amounts = re.findall(amount_pattern, line)
                  if dates and amounts:
                                    try:
                                                          date_str = dates[0]
                                                          for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                                                                                    try:
                                                                                                                  date = datetime.strptime(date_str, fmt)
                                                                                                                  break
                                                                                                              except:
                        continue
else:
                    continue
                amt = float(amounts[-1].replace(',', ''))
                desc = re.sub(date_pattern, '', line)
                desc = re.sub(amount_pattern, '', desc).strip()
                if 'DEBIT' in line.upper() or 'WITHDRAWAL' in line.upper() or 'PAYMENT' in line.upper():
                                          amt = -abs(amt)
                                      transactions.append({'Date': date, 'Description': desc, 'Amount': amt})
            except:
                continue
    return transactions

def calculate_enhanced_score(df, metrics):
          scores = {}
    # Revenue stability (30%)
    if metrics['avg_monthly_revenue'] > 50000:
                  scores['revenue'] = 95
elif metrics['avg_monthly_revenue'] > 30000:
        scores['revenue'] = 80
elif metrics['avg_monthly_revenue'] > 15000:
        scores['revenue'] = 65
elif metrics['avg_monthly_revenue'] > 5000:
        scores['revenue'] = 50
else:
        scores['revenue'] = 30
    # Debt burden (25%)
    debt_ratio = metrics['total_debt'] / max(metrics['total_revenue'], 1)
    if debt_ratio < 0.1:
                  scores['debt'] = 95
elif debt_ratio < 0.2:
        scores['debt'] = 80
elif debt_ratio < 0.35:
        scores['debt'] = 60
elif debt_ratio < 0.5:
        scores['debt'] = 40
else:
        scores['debt'] = 20
    # Cash cushion (20%)
    months_cushion = metrics['avg_balance'] / max(metrics['monthly_expenses'], 1)
    if months_cushion > 3:
                  scores['cash'] = 95
elif months_cushion > 2:
        scores['cash'] = 80
elif months_cushion > 1:
        scores['cash'] = 60
elif months_cushion > 0.5:
        scores['cash'] = 40
else:
        scores['cash'] = 20
    # NSF/Overdraft (15%)
    if metrics['nsf_count'] == 0:
                  scores['nsf'] = 100
elif metrics['nsf_count'] <= 2:
        scores['nsf'] = 70
elif metrics['nsf_count'] <= 5:
        scores['nsf'] = 40
else:
        scores['nsf'] = 10
    # Negative balance days (10%)
    neg_pct = metrics['negative_days'] / max(metrics['total_days'], 1)
    if neg_pct == 0:
                  scores['negative'] = 100
elif neg_pct < 0.05:
        scores['negative'] = 80
elif neg_pct < 0.15:
        scores['negative'] = 50
else:
        scores['negative'] = 20
    scores['overall'] = int(scores['revenue']*0.30 + scores['debt']*0.25 + scores['cash']*0.20 + scores['nsf']*0.15 + scores['negative']*0.10)
    return scores

def get_metrics(df):
          total_days = (df['Date'].max() - df['Date'].min()).days or 1
    months = total_days / 30
    revenue_df = df[df['tx_type'] == 'revenue']
    total_revenue = revenue_df['Amount'].sum()
    avg_monthly_revenue = total_revenue / max(months, 1)
    debt_df = df[df['tx_type'].isin(['mca_debt', 'loan'])]
    total_debt = abs(debt_df['Amount'].sum())
    expense_df = df[df['Amount'] < 0]
    monthly_expenses = abs(expense_df['Amount'].sum()) / max(months, 1)
    avg_balance = df['Balance'].mean()
    min_balance = df['Balance'].min()
    nsf_count = len(df[df['tx_type'] == 'fee'])
    negative_days = len(df[df['Balance'] < 0])
    return {'total_revenue': total_revenue, 'avg_monthly_revenue': avg_monthly_revenue, 'total_debt': total_debt, 'monthly_expenses': monthly_expenses, 'avg_balance': avg_balance, 'min_balance': min_balance, 'nsf_count': nsf_count, 'negative_days': negative_days, 'total_days': total_days}

# Sidebar
st.sidebar.title("🏦 Bank Statement Analyzer")
st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("📄 Upload Bank Statement (PDF)", type=['pdf'])

use_demo = st.sidebar.checkbox("Use Demo Data", value=True)

if uploaded_file and not use_demo:
          try:
                        import pdfplumber
                        with pdfplumber.open(uploaded_file) as pdf:
                                          text = ""
                                          for page in pdf.pages:
                                                                text += page.extract_text() or ""
                                                        transactions = parse_pdf_text(text)
                                      if transactions:
                            df = pd.DataFrame(transactions)
                                                        df = df.sort_values('Date').reset_index(drop=True)
                                                        result = df.apply(lambda r: categorize_transaction(r['Description'], r['Amount']), axis=1)
                                                        df['Category'] = [r[0] for r in result]
                                                        df['tx_type'] = [r[1] for r in result]
                                                        df['Confidence'] = [r[2] for r in result]
                                                        df['Balance'] = 10000 + df['Amount'].cumsum()
                                                        st.sidebar.success(f"✅ Parsed {len(df)} transactions")
                                      else:
                                                        st.sidebar.warning("Could not parse transactions")
                                                        use_demo = True
          except ImportError:
        st.sidebar.error("PDF parsing requires pdfplumber")
        use_demo = True
except Exception as e:
        st.sidebar.error(f"Error: {str(e)[:50]}")
        use_demo = True

if use_demo or 'df' not in dir():
          np.random.seed(42)
          n = 200
          df = pd.DataFrame({'Date': pd.date_range(end='2026-02-05', periods=n), 'Description': np.random.choice(['STRIPE TRANSFER', 'SQUARE INC', 'DAILY ACH DEBIT MCA', 'SBA LOAN PMT', 'ADP PAYROLL', 'RENT PAYMENT', 'UTILITY BILL', 'NSF FEE', 'SHOPIFY PAYOUT', 'MERCHANT CASH ADV'], n), 'Amount': np.random.uniform(-5000, 10000, n).round(2)})
          result = df.apply(lambda r: categorize_transaction(r['Description'], r['Amount']), axis=1)
          df['Category'] = [r[0] for r in result]
          df['tx_type'] = [r[1] for r in result]
          df['Confidence'] = [r[2] for r in result]
          df['Balance'] = 45000 + df['Amount'].cumsum()

metrics = get_metrics(df)
scores = calculate_enhanced_score(df, metrics)

st.sidebar.markdown("---")
st.sidebar.metric("Overall Score", f"{scores['overall']}/100")
st.sidebar.metric("Avg Monthly Revenue", f"${metrics['avg_monthly_revenue']:,.0f}")

# Main
st.title("🏦 Bank Statement Analyzer")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${metrics['total_revenue']:,.0f}")
c2.metric("Debt Payments", f"${metrics['total_debt']:,.0f}")
c3.metric("Avg Balance", f"${metrics['avg_balance']:,.0f}")
c4.metric("Min Balance", f"${metrics['min_balance']:,.0f}")

st.divider()
t1, t2, t3, t4, t5 = st.tabs(["📋 Transactions", "📈 Balance", "🎯 Scorecard", "💳 Debt", "🧠 Learning"])

with t1:
          st.subheader("Transaction History")
          cat_filter = st.multiselect("Filter Category", df['Category'].unique())
          show_df = df[df['Category'].isin(cat_filter)] if cat_filter else df
          st.dataframe(show_df[['Date', 'Description', 'Category', 'Amount', 'Balance', 'Confidence']], use_container_width=True)

with t2:
          st.subheader("Balance Trend")
          st.line_chart(df.set_index('Date')['Balance'])

with t3:
          st.subheader("Risk Scorecard")
          color = "🟢" if scores['overall'] >= 70 else "🟡" if scores['overall'] >= 50 else "🔴"
          st.markdown(f"## {color} {scores['overall']}/100")
          score_df = pd.DataFrame({'Factor': ['Revenue (30%)', 'Debt Burden (25%)', 'Cash Cushion (20%)', 'NSF/Fees (15%)', 'Negative Days (10%)'], 'Score': [scores['revenue'], scores['debt'], scores['cash'], scores['nsf'], scores['negative']]})
          st.dataframe(score_df, use_container_width=True)

with t4:
          st.subheader("Debt Analysis")
          mca_df = df[df['tx_type'] == 'mca_debt']
          loan_df = df[df['tx_type'] == 'loan']
          if len(mca_df) > 0:
                        st.error(f"⚠️ {len(mca_df)} MCA payments: ${abs(mca_df['Amount'].sum()):,.0f}")
                        st.dataframe(mca_df[['Date', 'Description', 'Amount']])
                    if len(loan_df) > 0:
                                  st.info(f"📊 {len(loan_df)} loan payments: ${abs(loan_df['Amount'].sum()):,.0f}")

with t5:
          st.subheader("🧠 Self-Learning System")
    st.markdown("Train the system to recognize new merchants")
    low_conf = df[df['Confidence'] < 0.7][['Description', 'Category', 'Amount']].drop_duplicates('Description')
    if len(low_conf) > 0:
                  st.warning(f"⚠️ {len(low_conf)} transactions need review")
                  for idx, row in low_conf.head(5).iterrows():
                                    col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(row['Description'][:40])
            new_cat = col2.selectbox("Category", ['Revenue', 'MCA Payment', 'Loan Payment', 'Payroll', 'Rent', 'Utilities', 'Other'], key=f"cat_{idx}")
            if col3.button("Learn", key=f"btn_{idx}"):
                                  tx_type = {'Revenue': 'revenue', 'MCA Payment': 'mca_debt', 'Loan Payment': 'loan'}.get(new_cat, 'operating')
                learn_merchant(row['Description'], new_cat, tx_type)
                st.success(f"Learned: {row['Description'][:20]}...")
    st.markdown("---")
    st.markdown(f"**Learned Patterns:** {len(st.session_state.learned_patterns)}")
    st.markdown(f"**Total Merchants in DB:** {len(st.session_state.merchant_db)}")
