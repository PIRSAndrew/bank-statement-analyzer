import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid
from collections import defaultdict
import statistics

# Page configuration
st.set_page_config(
      page_title="Bank Statement Analyzer",
      page_icon="🏦",
      layout="wide",
      initial_sidebar_state="expanded"
)

# Custom CSS for Heron-like styling
st.markdown("""
<style>
    .main-header {
            font-size: 2rem;
                    font-weight: bold;
                            margin-bottom: 1rem;
                                }
                                    .metric-card {
                                            background: white;
                                                    padding: 1rem;
                                                            border-radius: 8px;
                                                                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                                                        }
                                                                            .positive { color: #10b981; }
                                                                                .negative { color: #ef4444; }
                                                                                    .stTabs [data-baseweb="tab-list"] {
                                                                                            gap: 24px;
                                                                                                }
                                                                                                    .stTabs [data-baseweb="tab"] {
                                                                                                            padding: 10px 20px;
                                                                                                                }
                                                                                                                </style>
                                                                                                                """, unsafe_allow_html=True)

# ============================================================================
# DATA GENERATION (Demo Data)
# ============================================================================

@st.cache_data
def generate_demo_data():
      """Generate realistic demo bank statement data."""

    MERCHANTS = {
              'revenue': [
                            ('STRIPE TRANSFER', 'Revenue', True),
                            ('SQUARE INC', 'Revenue', True),
                            ('SHOPIFY PAYMENTS', 'Revenue', True),
                            ('PAYPAL TRANSFER', 'Revenue', True),
                            ('ACH DEPOSIT CUSTOMER PMT', 'Revenue', True),
              ],
              'mca_lenders': [
                            ('LIBERTAS FUNDING', 'Debt Repayment - MCA', 'mca'),
                            ('YELLOWSTONE CAPITAL', 'Debt Repayment - MCA', 'mca'),
                            ('FORWARD ADVANCES LLC', 'Debt Repayment - MCA', 'mca'),
              ],
              'traditional_lenders': [
                            ('ALLY BANK LOAN PMT', 'Debt Repayment', 'term_loan'),
                            ('WELLS FARGO LOAN', 'Debt Repayment', 'term_loan'),
              ],
              'payroll': [
                            ('GUSTO PAYROLL', 'Payroll and Consultants'),
                            ('ADP PAYROLL', 'Payroll and Consultants'),
              ],
              'utilities': [
                            ('DOMINION ENERGY', 'Utilities'),
                            ('VERIZON WIRELESS', 'Utilities'),
                            ('COMCAST BUSINESS', 'Utilities'),
              ],
              'software': [
                            ('AMAZON WEB SERVICES', 'Software'),
                            ('MICROSOFT 365', 'Software'),
                            ('SALESFORCE', 'Software'),
                            ('QUICKBOOKS ONLINE', 'Software'),
              ],
              'insurance': [
                            ('STATE FARM INSURANCE', 'Insurance'),
                            ('HARTFORD INSURANCE', 'Insurance'),
              ],
              'rent': [
                            ('COMMERCIAL PROPERTY MGMT', 'Rent'),
              ],
              'other': [
                            ('OFFICE DEPOT', 'Other expenses'),
                            ('THE UPS STORE', 'Postage'),
                            ('HARBOR FREIGHT TOOLS', 'Other expenses'),
              ],
    }

    transactions = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)
    current_date = start_date
    balance = 42163.79

    while current_date <= end_date:
              is_weekend = current_date.weekday() >= 5

        # Revenue deposits
              if not is_weekend and random.random() < 0.4:
                            merchant = random.choice(MERCHANTS['revenue'])
                            amount = round(random.uniform(50000, 250000), 2)
                            balance += amount
                            transactions.append({
                                'date': current_date.strftime('%Y-%m-%d'),
                                'description': merchant[0],
                                'amount': amount,
                                'balance': round(balance, 2),
                                'category': merchant[1],
                                'is_debit': False,
                                'is_true_revenue': True,
                                'is_debt_payment': False,
                                'debt_type': None,
                                'confidence': round(random.uniform(0.85, 0.98), 2)
                            })

              # MCA payments (daily)
              if random.random() < 0.7:
                            lender = random.choice(MERCHANTS['mca_lenders'])
                            amount = round(random.uniform(3500, 4500), 2)
                            balance -= amount
                            transactions.append({
                                'date': current_date.strftime('%Y-%m-%d'),
                                'description': lender[0],
                                'amount': -amount,
                                'balance': round(balance, 2),
                                'category': lender[1],
                                'is_debit': True,
                                'is_true_revenue': False,
                                'is_debt_payment': True,
                                'debt_type': lender[2],
                                'confidence': round(random.uniform(0.90, 0.99), 2)
                            })

        # Monthly bills
        if current_date.day <= 10:
                      if current_date.day <= 5 and random.random() < 0.2:
                                        merchant = MERCHANTS['rent'][0]
                                        amount = round(random.uniform(8000, 12000), 2)
                                        balance -= amount
                                        transactions.append({
                                            'date': current_date.strftime('%Y-%m-%d'),
                                            'description': merchant[0],
                                            'amount': -amount,
                                            'balance': round(balance, 2),
                                            'category': merchant[1],
                                            'is_debit': True,
                                            'is_true_revenue': False,
                                            'is_debt_payment': False,
                                            'debt_type': None,
                                            'confidence': round(random.uniform(0.85, 0.95), 2)
                                        })

                  # Payroll (bi-weekly)
                  if current_date.weekday() == 4 and current_date.day <= 15 and random.random() < 0.4:
                                merchant = random.choice(MERCHANTS['payroll'])
                                amount = round(random.uniform(25000, 50000), 2)
                                balance -= amount
                                transactions.append({
                                    'date': current_date.strftime('%Y-%m-%d'),
                                    'description': merchant[0],
                                    'amount': -amount,
                                    'balance': round(balance, 2),
                                    'category': merchant[1],
                                    'is_debit': True,
                                    'is_true_revenue': False,
                                    'is_debt_payment': False,
                                    'debt_type': None,
                                    'confidence': round(random.uniform(0.88, 0.96), 2)
                                })

        # Random daily expenses
        if not is_weekend:
                      for _ in range(random.randint(0, 2)):
                                        categories = ['utilities', 'software', 'other']
                                        cat = random.choice(categories)
                                        merchant = random.choice(MERCHANTS[cat])
                                        amount = round(random.uniform(50, 500), 2)
                                        balance -= amount
                                        transactions.append({
                                            'date': current_date.strftime('%Y-%m-%d'),
                                            'description': merchant[0],
                                            'amount': -amount,
                                            'balance': round(balance, 2),
                                            'category': merchant[1] if len(merchant) > 1 else 'Other',
                                            'is_debit': True,
                                            'is_true_revenue': False,
                                            'is_debt_payment': False,
                                            'debt_type': None,
                                            'confidence': round(random.uniform(0.75, 0.92), 2)
                                        })

                  current_date += timedelta(days=1)

    return pd.DataFrame(transactions)

# ============================================================================
# CALCULATIONS
# ============================================================================

def calculate_monthly_summary(df):
      """Calculate bank statement summary by month."""
      df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)

    summaries = []
    for month in sorted(df['month'].unique()):
              month_df = df[df['month'] == month]

        deposits = month_df[month_df['amount'] > 0]
        withdrawals = month_df[month_df['amount'] < 0]
        true_rev = month_df[month_df['is_true_revenue'] == True]
        mca = month_df[month_df['debt_type'] == 'mca']

        total_deposits = deposits['amount'].sum()
        total_withdrawals = abs(withdrawals['amount'].sum())
        total_true_revenue = true_rev['amount'].sum()
        total_mca = abs(mca['amount'].sum())

        balances = month_df['balance'].tolist()
        ending_balance = balances[-1] if balances else 0
        avg_balance = statistics.mean(balances) if balances else 0

        holdback_pct = (total_mca / total_true_revenue * 100) if total_true_revenue > 0 else 0
        negative_days = sum(1 for b in balances if b < 0)

        summaries.append({
                      'Month': month,
                      'Starting Balance': f"${balances[0]:,.2f}" if balances else "$0.00",
                      '# Deposits': len(deposits),
                      'Total Deposits': f"${total_deposits:,.2f}",
                      'True Revenue': f"${total_true_revenue:,.2f}",
                      '# Withdrawals': len(withdrawals),
                      'Total Withdrawals': f"${total_withdrawals:,.2f}",
                      'MCA Debits': f"${total_mca:,.2f}",
                      'Holdback %': f"{holdback_pct:.2f}%",
                      'Ending Balance': f"${ending_balance:,.2f}",
                      'Avg Balance': f"${avg_balance:,.2f}",
                      'Neg Balance Days': negative_days
        })

    return pd.DataFrame(summaries)

def calculate_debt_summary(df):
      """Calculate debt summary from transactions."""
      debt_df = df[df['is_debt_payment'] == True].copy()

    if debt_df.empty:
              return pd.DataFrame()

    debt_summary = []
    for lender in debt_df['description'].unique():
              lender_df = debt_df[debt_df['description'] == lender]
              amounts = abs(lender_df['amount'])
              dates = pd.to_datetime(lender_df['date']).sort_values()

        if len(dates) >= 2:
                      intervals = dates.diff().dt.days.dropna()
                      avg_interval = intervals.mean()
                      if avg_interval <= 2:
                                        frequency = 'daily'
                                        est_monthly = amounts.mean() * 22
        elif avg_interval <= 9:
                frequency = 'weekly'
                est_monthly = amounts.mean() * 4
else:
                frequency = 'monthly'
                  est_monthly = amounts.mean()
else:
            frequency = 'monthly'
            est_monthly = amounts.mean()

        debt_type = lender_df['debt_type'].iloc[0]
        group = 'Merchant Cash Advance' if debt_type == 'mca' else 'Term Loan'

        debt_summary.append({
                      'Lender': lender,
                      'Group': group,
                      'First Date': dates.min().strftime('%Y-%m-%d'),
                      'Last Date': dates.max().strftime('%Y-%m-%d'),
                      'Active': '✓',
                      'Count': len(lender_df),
                      'Total Amount': f"${amounts.sum():,.2f}",
                      'Avg Amount': f"${amounts.mean():,.2f}",
                      'Frequency': frequency,
                      'Est. Monthly': f"${est_monthly:,.2f}"
        })

    return pd.DataFrame(debt_summary)

def calculate_scorecard(df):
      """Calculate scorecard metrics."""
    metrics = []

    balances = df['balance'].tolist()
    inflows = df[df['amount'] > 0]['amount']
    true_revenue = df[df['is_true_revenue'] == True]['amount']
    debt_payments = df[df['is_debt_payment'] == True]['amount']
    mca_payments = df[df['debt_type'] == 'mca']['amount']

    # Balance metrics
    metrics.append({'Type': 'balance', 'Metric': 'Latest Balance', 'Value': f"${balances[-1]:,.2f}", 'Status': '✓'})
    metrics.append({'Type': 'balance', 'Metric': 'Balance Average (30 days)', 'Value': f"${statistics.mean(balances[-30:]):,.2f}", 'Status': '✓'})
    metrics.append({'Type': 'balance', 'Metric': 'Balance Minimum (30 days)', 'Value': f"${min(balances[-30:]):,.2f}", 'Status': '✓' if min(balances[-30:]) > 0 else '⚠'})
    metrics.append({'Type': 'balance', 'Metric': 'Balance Maximum (30 days)', 'Value': f"${max(balances[-30:]):,.2f}", 'Status': '✓'})

    # Data quality metrics
    metrics.append({'Type': 'data_quality', 'Metric': 'Data Volume', 'Value': str(len(df)), 'Status': '✓'})
    metrics.append({'Type': 'data_quality', 'Metric': 'True Revenue (Total)', 'Value': f"${true_revenue.sum():,.2f}", 'Status': '✓'})
    metrics.append({'Type': 'data_quality', 'Metric': 'Avg Confidence', 'Value': f"{df['confidence'].mean()*100:.1f}%", 'Status': '✓'})

    # Debt metrics
    if len(mca_payments) > 0:
              holdback = abs(mca_payments.sum()) / true_revenue.sum() * 100 if true_revenue.sum() > 0 else 0
        metrics.append({'Type': 'debt', 'Metric': 'MCA Payments (Total)', 'Value': f"${abs(mca_payments.sum()):,.2f}", 'Status': '⚠'})
        metrics.append({'Type': 'debt', 'Metric': 'Holdback %', 'Value': f"{holdback:.2f}%", 'Status': '✓' if holdback < 15 else '⚠'})

    return pd.DataFrame(metrics)

# ============================================================================
# MAIN APP
# ============================================================================

def main():
      # Sidebar
      with st.sidebar:
                st.image("https://img.icons8.com/color/96/000000/bank-building.png", width=50)
        st.title("Bank Analyzer")

        st.markdown("---")
        st.markdown("**End User**")
        st.markdown("demo_user_12345")
        st.success("Processed")

        st.markdown("---")
        st.markdown("**Navigation**")

        page = st.radio(
                      "Select Page",
                      ["📊 Bank & Debt Summary", "💳 Transactions", "📈 Balance Insights", "📋 Scorecard"],
                      label_visibility="collapsed"
        )

    # Load demo data
    df = generate_demo_data()

    # Main content
    if "Bank & Debt Summary" in page:
              st.markdown("## 📊 Bank Statement Summary")

        # Monthly summary
        st.markdown("### Monthly Summary")
        monthly_df = calculate_monthly_summary(df.copy())
        st.dataframe(monthly_df, use_container_width=True, hide_index=True)

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        total_revenue = df[df['is_true_revenue'] == True]['amount'].sum()
        total_deposits = df[df['amount'] > 0]['amount'].sum()
        total_withdrawals = abs(df[df['amount'] < 0]['amount'].sum())
        total_mca = abs(df[df['debt_type'] == 'mca']['amount'].sum())

        col1.metric("Total True Revenue", f"${total_revenue:,.2f}")
        col2.metric("Total Deposits", f"${total_deposits:,.2f}")
        col3.metric("Total Withdrawals", f"${total_withdrawals:,.2f}")
        col4.metric("MCA Payments", f"${total_mca:,.2f}")

        st.markdown("---")

        # Debt Summary
        st.markdown("### 💰 Debt Summary")
        debt_df = calculate_debt_summary(df)
        if not debt_df.empty:
                      st.dataframe(debt_df, use_container_width=True, hide_index=True)
else:
            st.info("No debt payments detected")

        # Recurring transactions
        st.markdown("### 🔄 Recurring Transactions")
        recurring = df.groupby('description').agg({
                      'amount': ['count', 'sum', 'mean'],
                      'date': ['min', 'max'],
                      'category': 'first'
        }).reset_index()
        recurring.columns = ['Merchant', 'Count', 'Total', 'Avg Amount', 'First Date', 'Last Date', 'Category']
        recurring = recurring[recurring['Count'] >= 3].sort_values('Count', ascending=False)
        recurring['Total'] = recurring['Total'].apply(lambda x: f"${abs(x):,.2f}")
        recurring['Avg Amount'] = recurring['Avg Amount'].apply(lambda x: f"${abs(x):,.2f}")
        st.dataframe(recurring.head(15), use_container_width=True, hide_index=True)

elif "Transactions" in page:
        st.markdown("## 💳 Transactions")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
                      categories = ['All'] + list(df['category'].unique())
                      selected_cat = st.selectbox("Category", categories)
                  with col2:
                                min_amount = st.number_input("Min Amount", value=0.0)
                            with col3:
                                          search = st.text_input("Search Description")

        # Filter data
        filtered_df = df.copy()
        if selected_cat != 'All':
                      filtered_df = filtered_df[filtered_df['category'] == selected_cat]
                  if min_amount > 0:
                                filtered_df = filtered_df[abs(filtered_df['amount']) >= min_amount]
                            if search:
                                          filtered_df = filtered_df[filtered_df['description'].str.contains(search, case=False)]

        # Display
        display_df = filtered_df[['date', 'description', 'amount', 'balance', 'category', 'confidence']].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
        display_df['balance'] = display_df['balance'].apply(lambda x: f"${x:,.2f}")
        display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x*100:.0f}%")
        display_df.columns = ['Date', 'Description', 'Amount', 'Balance', 'Category', 'Confidence']

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
        st.caption(f"Showing {len(filtered_df)} transactions")

elif "Balance Insights" in page:
        st.markdown("## 📈 Balance Insights")

        # Balance over time chart
        chart_df = df[['date', 'balance']].copy()
        chart_df['date'] = pd.to_datetime(chart_df['date'])
        chart_df = chart_df.groupby('date')['balance'].last().reset_index()

        st.line_chart(chart_df.set_index('date')['balance'])

        # Stats
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Balance", f"${df['balance'].iloc[-1]:,.2f}")
        col2.metric("Average Balance", f"${df['balance'].mean():,.2f}")
        col3.metric("Min Balance", f"${df['balance'].min():,.2f}")
        col4.metric("Max Balance", f"${df['balance'].max():,.2f}")

elif "Scorecard" in page:
        st.markdown("## 📋 Scorecard Metrics")

        scorecard_df = calculate_scorecard(df)

        for metric_type in scorecard_df['Type'].unique():
                      st.markdown(f"### {metric_type.replace('_', ' ').title()}")
                      type_df = scorecard_df[scorecard_df['Type'] == metric_type][['Metric', 'Value', 'Status']]
                      st.dataframe(type_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
      main()
