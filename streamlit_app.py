import streamlit as st
import pandas as pd
import pdfplumber
import re
import json
from datetime import datetime
from collections import defaultdict

if 'learned_patterns' not in st.session_state:
    st.session_state.learned_patterns = {}

CATEGORIES = {
    'MCA_DEBT': ['daily ach', 'merchant cash', 'fundbox', 'kabbage', 'ondeck', 'bluevine', 'credibly', 'rapid finance', 'forward financing', 'clearco', 'shopify capital'],
    'LOAN_PAYMENT': ['loan pmt', 'loan payment', 'sba loan', 'term loan', 'lending club', 'prosper', 'funding circle'],
    'RENT': ['rent', 'lease', 'property mgmt', 'landlord'],
    'PAYROLL': ['payroll', 'gusto', 'adp', 'paychex', 'quickbooks payroll', 'square payroll'],
    'UTILITIES': ['electric', 'gas bill', 'water bill', 'utility', 'pge', 'edison', 'comcast', 'att', 'verizon'],
    'INSURANCE': ['insurance', 'geico', 'allstate', 'progressive', 'state farm'],
    'REVENUE': ['deposit', 'payment received', 'stripe', 'square', 'paypal', 'shopify', 'amazon payout', 'pos deposit'],
    'TRANSFER_IN': ['transfer from', 'xfer from', 'mobile deposit'],
    'TRANSFER_OUT': ['transfer to', 'xfer to', 'wire out'],
    'TAX': ['irs', 'tax payment', 'estimated tax', 'state tax', 'franchise tax'],
    'CREDIT_CARD': ['credit card', 'amex', 'chase card', 'visa payment', 'mastercard'],
    'OTHER_EXPENSE': []
}

def extract_transactions_from_pdf(pdf_file):
    transactions = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
            lines = full_text.split('\n')
            date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]?\d{0,4})'
            amount_pattern = r'[\$]?([\d,]+\.\d{2})'
            for line in lines:
                date_match = re.search(date_pattern, line)
                amounts = re.findall(amount_pattern, line)
                if date_match and amounts:
                    desc = re.sub(date_pattern, '', line)
                    desc = re.sub(amount_pattern, '', desc).strip()
                    if len(desc) > 3:
                        amount = float(amounts[-1].replace(',', ''))
                        if any(word in line.lower() for word in ['debit', 'withdrawal', 'payment', 'purchase', '-']):
                            amount = -abs(amount)
                        transactions.append({'date': date_match.group(1), 'description': desc[:50], 'amount': amount})
    except Exception as e:
        st.error(f"Error parsing PDF: {str(e)}")
    return transactions

def categorize_transaction(description, amount):
    desc_lower = description.lower()
    for pattern, category in st.session_state.learned_patterns.items():
        if pattern.lower() in desc_lower:
            return category
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if pattern in desc_lower:
                return category
    if amount > 0:
        return 'REVENUE'
    return 'OTHER_EXPENSE'

def identify_recurring(transactions):
    from collections import defaultdict
    desc_amounts = defaultdict(list)
    for t in transactions:
        key = t['description'][:20].lower()
        desc_amounts[key].append(t['amount'])
    recurring = []
    for desc, amounts in desc_amounts.items():
        if len(amounts) >= 2:
            avg_amount = sum(amounts) / len(amounts)
            if all(abs(a - avg_amount) < abs(avg_amount) * 0.1 for a in amounts):
                recurring.append({'pattern': desc, 'avg_amount': avg_amount, 'frequency': len(amounts)})
    return recurring

def calculate_score(df):
    score = 100
    revenue = df[df['amount'] > 0]['amount'].sum()
    expenses = abs(df[df['amount'] < 0]['amount'].sum())
    if expenses > 0:
        ratio = revenue / expenses
        if ratio < 1:
            score -= 30
        elif ratio < 1.5:
            score -= 15
    debt_categories = ['MCA_DEBT', 'LOAN_PAYMENT', 'CREDIT_CARD']
    debt = abs(df[df['category'].isin(debt_categories)]['amount'].sum())
    debt_ratio = debt / revenue if revenue > 0 else 1
    if debt_ratio > 0.3:
        score -= 25
    elif debt_ratio > 0.15:
        score -= 12
    if df['amount'].std() > abs(df['amount'].mean()) * 2:
        score -= 20
    elif df['amount'].std() > abs(df['amount'].mean()):
        score -= 10
    nsf_count = len(df[df['description'].str.lower().str.contains('nsf|overdraft|insufficient', na=False)])
    score -= min(nsf_count * 5, 15)
    negative_count = len(df[df['amount'] < 0])
    if negative_count > len(df) * 0.7:
        score -= 10
    return max(0, min(100, score))

st.set_page_config(page_title="Bank Statement Analyzer", layout="wide")
st.title("Bank Statement Analyzer")

with st.sidebar:
    st.header("Upload Statement")
    uploaded_file = st.file_uploader("Upload PDF Bank Statement", type=['pdf'])
    st.header("Train New Pattern")
    new_pattern = st.text_input("Transaction text to match:")
    new_category = st.selectbox("Assign to category:", list(CATEGORIES.keys()))
    if st.button("Add Pattern"):
        if new_pattern:
            st.session_state.learned_patterns[new_pattern] = new_category
            st.success(f"Learned: '{new_pattern}' -> {new_category}")
    if st.session_state.learned_patterns:
        st.subheader("Learned Patterns")
        for p, c in st.session_state.learned_patterns.items():
            st.text(f"{p[:20]}... -> {c}")

if uploaded_file:
    transactions = extract_transactions_from_pdf(uploaded_file)
    if transactions:
        df = pd.DataFrame(transactions)
        df['category'] = df.apply(lambda x: categorize_transaction(x['description'], x['amount']), axis=1)
        col1, col2, col3, col4 = st.columns(4)
        revenue = df[df['amount'] > 0]['amount'].sum()
        expenses = abs(df[df['amount'] < 0]['amount'].sum())
        col1.metric("Total Revenue", f"${revenue:,.2f}")
        col2.metric("Total Expenses", f"${expenses:,.2f}")
        col3.metric("Net Cash Flow", f"${revenue - expenses:,.2f}")
        col4.metric("Health Score", f"{calculate_score(df)}/100")
        st.subheader("Transaction Categories")
        category_summary = df.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        category_summary.columns = ['Category', 'Total Amount', 'Count']
        st.dataframe(category_summary, use_container_width=True)
        st.subheader("Debt Analysis")
        debt_df = df[df['category'].isin(['MCA_DEBT', 'LOAN_PAYMENT', 'CREDIT_CARD'])]
        if not debt_df.empty:
            st.dataframe(debt_df, use_container_width=True)
            st.metric("Total Debt Payments", f"${abs(debt_df['amount'].sum()):,.2f}")
        else:
            st.info("No debt payments detected")
        st.subheader("Recurring Transactions (Potential Debt)")
        recurring = identify_recurring(transactions)
        if recurring:
            for r in recurring:
                st.write(f"**{r['pattern']}**: ${abs(r['avg_amount']):,.2f} x {r['frequency']} times")
        st.subheader("All Transactions")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No transactions found in PDF. Try a different file.")
else:
    st.info("Upload a PDF bank statement to begin analysis")
    if st.button("Load Demo Data"):
        demo_data = [
            {'date': '01/05', 'description': 'STRIPE DEPOSIT', 'amount': 15000},
            {'date': '01/06', 'description': 'DAILY ACH FUNDBOX', 'amount': -450},
            {'date': '01/07', 'description': 'GUSTO PAYROLL', 'amount': -3500},
            {'date': '01/10', 'description': 'SHOPIFY PAYOUT', 'amount': 8500},
            {'date': '01/12', 'description': 'ONDECK LOAN PMT', 'amount': -800},
            {'date': '01/15', 'description': 'RENT PAYMENT', 'amount': -2500},
            {'date': '01/18', 'description': 'AMAZON PAYOUT', 'amount': 12000},
            {'date': '01/20', 'description': 'DAILY ACH FUNDBOX', 'amount': -450},
            {'date': '01/22', 'description': 'PGE UTILITY', 'amount': -350},
            {'date': '01/25', 'description': 'SQUARE DEPOSIT', 'amount': 6500},
        ]
        df = pd.DataFrame(demo_data)
        df['category'] = df.apply(lambda x: categorize_transaction(x['description'], x['amount']), axis=1)
        col1, col2, col3, col4 = st.columns(4)
        revenue = df[df['amount'] > 0]['amount'].sum()
        expenses = abs(df[df['amount'] < 0]['amount'].sum())
        col1.metric("Total Revenue", f"${revenue:,.2f}")
        col2.metric("Total Expenses", f"${expenses:,.2f}")
        col3.metric("Net Cash Flow", f"${revenue - expenses:,.2f}")
        col4.metric("Health Score", f"{calculate_score(df)}/100")
        st.subheader("Categorized Transactions")
        st.dataframe(df, use_container_width=True)
