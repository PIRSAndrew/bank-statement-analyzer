"""
Bank Statement Analyzer v2 - Phase 1 with persistence and auth
Refactored to use SQLAlchemy ORM and Supabase authentication
"""

import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime
from auth import init_auth_state, is_authenticated, render_auth_page, require_auth, render_user_menu
from database import (
    SessionLocal, get_user_statements, create_statement, add_transactions_bulk,
    get_statement, get_statement_transactions, get_user_patterns, save_learned_pattern,
    update_transaction_category, delete_statement
)

# Categories for transaction classificationh
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


# ==================== PDF EXTRACTION ====================

def extract_transactions_from_pdf(pdf_file):
    """Extract transactions from PDF file"""
    transactions = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        lines = full_text.split('\n')
        for line in lines:
            date_match = re.search(r'(\d{1,2}/[\d{1,2}/)*]d{0,4})', line)
            amounts = re.findall(r'(\$)([,\d.]+\.\d{2})', line)
            if date_match and amounts:
                desc = re.sub(r'[\d\s/\$,.-]+', '', line)
                desc = re.sub(r'  +', ' ', desc).strip()
                if len(desc) > 3:
                    amount = float(amounts[-1][1].replace(',', ''))
                    transactions.append({
                        'date': date_match.group(1),
                        'description': desc[:50],
                        'amount': amount
                    })
    except Exception as e:
        st.error(f"Error parsing PDF: {str(e)}")
    return transactions

# ==================== CATEGORIZATION ====================

def categorize_transaction(description, amount, user_patterns):
    """Categorize transaction using learned patterns and categories"""
    desc_lower = description.lower()

    # Check learned patterns first (user has highest priority)
    for pattern in user_patterns:
        if pattern.pattern.lower() in desc_lower:
            return pattern.category, pattern.confidence

    # Then check default categories
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if pattern in desc_lower:
                return category, 1.0

    # Default based on amount
    if amount > 0:
        return 'REVENUE', 0.5
    return 'OTHER_EXPENSE', 0.5

def calculate_score(transactions_list):
    """Calculate financial health score"""
    if not transactions_list:
        return 0

    df = pd.DataFrame(transactions_list)
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

# ==================== UI SETUP ====================

st.set_page_config(page_title="Bank Statement Analyzer", layout="wide")

# Initialize auth state
init_auth_state()

# Show login page if not authenticated
if not is_authenticated():
    render_auth_page()
    st.stop()

# User is authenticated - show main app
st.title("🏦 Bank Statement Analyzer")

# Sidebar
with st.sidebar:
    st.header("📊 Dashboard")
    render_user_menu()

    st.markdown("---")
    st.header("📤 Upload Statement")

    uploaded_file = st.file_uploader("Upload PDF Bank Statement", type=['pdf'])

    st.markdown("---")
    st.header("🎓 Train New Pattern")

    new_pattern = st.text_input("Transaction text to match:")
    new_category = st.selectbox("Assign to category:", list(CATEGORIES.keys()))

    if st.button("Add Pattern", use_container_width=True):
        if new_pattern:
            db = SessionLocal()
            save_learned_pattern(db, st.session_state.user_id, new_pattern, new_category)
            db.close()
            st.success(f"✅ Learned: '{new_pattern}' → {new_category}")
            st.rerun()
        else:
            st.error("❌ Please enter a pattern")

    # Show learned patterns
    db = SessionLocal()
    learned_patterns = get_user_patterns(db, st.session_state.user_id)
    db.close()

    if learned_patterns:
        st.markdown("**Learned Patterns:**")
        for pattern in learned_patterns:
            st.caption(f"'{pattern.pattern[:20]}...' → {pattern.category} (used {pattern.times_used}x)")
# Main content area
if uploaded_file:
    st.subheader("📋 Analysis Results")

    # Extract transactions
    transactions = extract_transactions_from_pdf(uploaded_file)

    if transactions:
        # Get learned patterns for categorization
        db = SessionLocal()
        user_patterns = get_user_patterns(db, st.session_state.user_id)

        # Categorize transactions
        for txn in transactions:
            category, confidence = categorize_transaction(txn['description'], txn['amount'], user_patterns)
            txn['category'] = category
            txn['category_confidence'] = confidence

        # Save to database
        statement_data = {
            'statement_month': datetime.now().strftime("%Y-%m"),
            'total_transactions': len(transactions),
            'total_revenue': sum(t['amount'] for t in transactions if t['amount'] > 0),
            'total_expenses': abs(sum(t['amount'] for t in transactions if t['amount'] < 0)),
            'net_cash_flow': sum(t['amount'] for t in transactions),
            'health_score': calculate_score(transactions),
            'raw_data': transactions
        }

        statement = create_statement(db, st.session_state.user_id, uploaded_file.name, statement_data)
        add_transactions_bulk(db, statement.id, transactions)
        db.commit()

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"${statement_data['total_revenue']:,.2f}")
        col2.metric("Total Expenses", f"${statement_data['total_expenses']:,.2f}")
        col3.metric("Net Cash Flow", f"${statement_data['net_cash_flow']:,.2f}")
        col4.metric("Health Score", f"{int(statement_data['health_score'])}/100")

        # Transaction breakdown
        df = pd.DataFrame(transactions)

        st.subheader("Transaction Categories")
        category_summary = df.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        category_summary.columns = ['Category', 'Total Amount', 'Count']
        st.dataframe(category_summary, use_container_width=True)

        st.subheader("All Transactions")
        st.dataframe(df, use_container_width=True)

        st.success(f"✅ Statement saved! ID: {statement.id}")
        db.close()
    else:
        st.warning("❌ No transactions found in PDF")

else:
    st.info("👈 Upload a PDF bank statement to begin analysis")

# Show recent statements
db = SessionLocal()
recent_statements = get_user_statements(db, st.session_state.user_id)

if recent_statements:
    st.subheader("📚 Recent Statements")

    for stmt in recent_statements[:5]:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

        with col1:
            st.write(f"**{stmt.filename}**")
        with col2:
            st.write(f"{stmt.upload_date.strftime('%Y-%m-%d')}")
        with col3:
            st.write(f"${stmt.net_cash_flow:,.2f}")
        with col4:
            st.write(f"Score: {stmt.health_score:.0f}/100")
        with col5:
            if st.button("View", key=f"view_{stmt.id}"):
                # Load and display this statement
                transactions = get_statement_transactions(db, stmt.id)
                df = pd.DataFrame([{
                    'date': t.date,
                    'description': t.description,
                    'amount': t.amount,
                    'category': t.category
                } for t in transactions])

                st.write(df)

db.close()
