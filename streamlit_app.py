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

# =============================================================================
# DATA GENERATION (Demo Data)
# =============================================================================

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
                                    ('WIRE TRANSFER IN', 'Revenue', True),
                  ],
                  'non_revenue': [
                                    ('TRANSFER FROM SAVINGS', 'Transfer', False),
                                    ('LOAN PROCEEDS', 'Loan', False),
                                    ('OWNER CONTRIBUTION', 'Capital', False),
                                    ('TAX REFUND', 'Tax', False),
                  ],
                  'mca_debt': [
                                    ('DAILY ACH DEBIT MCA', 'MCA Payment', True),
                                    ('MERCHANT CASH ADV', 'MCA Payment', True),
                                    ('BUSINESS FUNDING PMT', 'MCA Payment', True),
                                    ('RAPID ADVANCE PYMT', 'MCA Payment', True),
                  ],
                  'regular_debt': [
                                    ('LOAN PAYMENT', 'Loan Payment', True),
                                    ('SBA LOAN PMT', 'Loan Payment', True),
                                    ('EQUIPMENT LEASE', 'Lease Payment', True),
                                    ('LINE OF CREDIT PMT', 'LOC Payment', True),
                  ],
                  'operating': [
                                    ('RENT PAYMENT', 'Rent', True),
                                    ('PAYROLL', 'Payroll', True),
                                    ('ADP PAYROLL', 'Payroll', True),
                                    ('GUSTO PAYROLL', 'Payroll', True),
                                    ('UTILITIES', 'Utilities', True),
                                    ('INSURANCE PMT', 'Insurance', True),
                                    ('SUPPLIES', 'Supplies', False),
                                    ('AMAZON BUSINESS', 'Supplies', False),
                                    ('OFFICE DEPOT', 'Supplies', False),
                  ],
                  'fees': [
                                    ('BANK FEE', 'Bank Fee', False),
                                    ('NSF FEE', 'NSF Fee', False),
                                    ('OVERDRAFT FEE', 'Overdraft Fee', False),
                                    ('WIRE FEE', 'Wire Fee', False),
                  ]
    }

    # Generate 90 days of transactions
    transactions = []
    start_date = datetime.now() - timedelta(days=90)
    balance = 45000.00

    for day in range(90):
                  current_date = start_date + timedelta(days=day)

        # Skip some weekends for realistic data
                  if current_date.weekday() >= 5 and random.random() < 0.7:
                                    continue

                  # Daily transactions
                  num_transactions = random.randint(1, 6)

        for _ in range(num_transactions):
                          # Determine transaction type with weighted probability
                          tx_type = random.choices(
                                                ['revenue', 'non_revenue', 'mca_debt', 'regular_debt', 'operating', 'fees'],
                                                weights=[25, 5, 15, 10, 40, 5]
                          )[0]

            merchant_info = random.choice(MERCHANTS[tx_type])
            merchant_name, category, is_recurring = merchant_info

            # Generate amount based on type
            if tx_type == 'revenue':
                                  amount = round(random.uniform(500, 15000), 2)
elif tx_type == 'non_revenue':
                      amount = round(random.uniform(1000, 50000), 2)
elif tx_type == 'mca_debt':
                      amount = -round(random.uniform(200, 800), 2)
elif tx_type == 'regular_debt':
                      amount = -round(random.uniform(500, 3000), 2)
elif tx_type == 'operating':
                      amount = -round(random.uniform(100, 8000), 2)
else:  # fees
                      amount = -round(random.uniform(25, 150), 2)

            balance += amount

            transactions.append({
                                  'id': str(uuid.uuid4())[:8],
                                  'date': current_date.strftime('%Y-%m-%d'),
                                  'description': merchant_name + f" {random.randint(1000, 9999)}",
                                  'amount': amount,
                                  'balance': round(balance, 2),
                                  'category': category,
                                  'is_recurring': is_recurring,
                                  'tx_type': tx_type
            })

    return pd.DataFrame(transactions)

def calculate_metrics(df):
          """Calculate key financial metrics from transaction data."""

    # Revenue metrics
          revenue_df = df[df['tx_type'] == 'revenue']
    total_revenue = revenue_df['amount'].sum()
    avg_monthly_revenue = total_revenue / 3

    # Debt metrics
    mca_df = df[df['tx_type'] == 'mca_debt']
    regular_debt_df = df[df['tx_type'] == 'regular_debt']
    total_mca = abs(mca_df['amount'].sum())
    total_debt_payments = abs(regular_debt_df['amount'].sum()) + total_mca

    # Operating expenses
    operating_df = df[df['tx_type'] == 'operating']
    total_operating = abs(operating_df['amount'].sum())

    # Balance metrics
    ending_balance = df.iloc[-1]['balance'] if len(df) > 0 else 0
    avg_balance = df['balance'].mean()
    min_balance = df['balance'].min()

    # NSF/Overdraft
    fees_df = df[df['tx_type'] == 'fees']
    nsf_count = len(fees_df[fees_df['category'].isin(['NSF Fee', 'Overdraft Fee'])])

    # Negative days
    negative_days = len(df[df['balance'] < 0]['date'].unique())

    return {
                  'total_revenue': total_revenue,
                  'avg_monthly_revenue': avg_monthly_revenue,
                  'total_mca': total_mca,
                  'total_debt_payments': total_debt_payments,
                  'total_operating': total_operating,
                  'ending_balance': ending_balance,
                  'avg_balance': avg_balance,
                  'min_balance': min_balance,
                  'nsf_count': nsf_count,
                  'negative_days': negative_days
    }

def calculate_scorecard(metrics):
          """Calculate risk scorecard similar to Heron."""

    scores = {}

    # Revenue Score (0-100)
    if metrics['avg_monthly_revenue'] > 50000:
                  scores['revenue'] = 95
elif metrics['avg_monthly_revenue'] > 30000:
              scores['revenue'] = 80
elif metrics['avg_monthly_revenue'] > 15000:
              scores['revenue'] = 65
else:
              scores['revenue'] = 45

    # Debt Burden Score
          debt_ratio = metrics['total_debt_payments'] / max(metrics['total_revenue'], 1)
    if debt_ratio < 0.1:
                  scores['debt_burden'] = 95
elif debt_ratio < 0.2:
              scores['debt_burden'] = 75
elif debt_ratio < 0.35:
              scores['debt_burden'] = 55
else:
              scores['debt_burden'] = 30

    # Cash Flow Score
          if metrics['avg_balance'] > 20000:
                        scores['cash_flow'] = 90
elif metrics['avg_balance'] > 10000:
              scores['cash_flow'] = 70
elif metrics['avg_balance'] > 5000:
              scores['cash_flow'] = 50
else:
              scores['cash_flow'] = 30

    # NSF Score
          if metrics['nsf_count'] == 0:
                        scores['nsf'] = 100
elif metrics['nsf_count'] <= 2:
              scores['nsf'] = 70
elif metrics['nsf_count'] <= 5:
              scores['nsf'] = 40
else:
              scores['nsf'] = 20

    # Overall Score
          scores['overall'] = int(
                        scores['revenue'] * 0.3 +
                        scores['debt_burden'] * 0.25 +
                        scores['cash_flow'] * 0.25 +
                        scores['nsf'] * 0.2
          )

    return scores

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
          # Sidebar
          st.sidebar.title("🏦 Bank Statement Analyzer")
          st.sidebar.markdown("---")

    # Demo mode notice
          st.sidebar.info("📊 **Demo Mode**\nViewing sample transaction data")

    # File upload placeholder
    uploaded_file = st.sidebar.file_uploader(
                  "Upload Bank Statement (PDF)",
                  type=['pdf'],
                  help="Upload a PDF bank statement for analysis"
    )

    if uploaded_file:
                  st.sidebar.success("File uploaded! (Demo data shown)")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")

    # Load demo data
    df = generate_demo_data()
    metrics = calculate_metrics(df)
    scores = calculate_scorecard(metrics)

    # Sidebar quick stats
    st.sidebar.metric("Overall Score", f"{scores['overall']}/100")
    st.sidebar.metric("Avg Monthly Revenue", f"${metrics['avg_monthly_revenue']:,.0f}")
    st.sidebar.metric("Current Balance", f"${metrics['ending_balance']:,.2f}")

    # Main content area
    st.markdown("## 📊 Bank & Debt Summary")

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
                  st.metric(
                                    "Total Revenue (90 days)",
                                    f"${metrics['total_revenue']:,.2f}",
                                    delta=f"${metrics['avg_monthly_revenue']:,.0f}/mo avg"
                  )

    with col2:
                  st.metric(
                                    "Total Debt Payments",
                                    f"${metrics['total_debt_payments']:,.2f}",
                                    delta=f"-${metrics['total_mca']:,.0f} MCA",
                                    delta_color="inverse"
                  )

    with col3:
                  st.metric(
                                    "Operating Expenses",
                                    f"${metrics['total_operating']:,.2f}"
                  )

    with col4:
                  st.metric(
                                    "Ending Balance",
                                    f"${metrics['ending_balance']:,.2f}",
                                    delta=f"Min: ${metrics['min_balance']:,.2f}"
                  )

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Transactions", "📈 Balance Insights", "🎯 Scorecard", "💳 Debt Analysis"])

    with tab1:
                  st.markdown("### Transaction History")

        # Filters
                  col1, col2, col3 = st.columns(3)
        with col1:
                          category_filter = st.multiselect(
                                                "Filter by Category",
                                                options=df['category'].unique(),
                                                default=[]
                          )
                      with col2:
                                        tx_type_filter = st.multiselect(
                                                              "Filter by Type",
                                                              options=['revenue', 'mca_debt', 'regular_debt', 'operating', 'fees'],
                                                              default=[]
                                        )
                                    with col3:
                                                      show_recurring = st.checkbox("Show Recurring Only", value=False)

        # Apply filters
        filtered_df = df.copy()
        if category_filter:
                          filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]
                      if tx_type_filter:
                                        filtered_df = filtered_df[filtered_df['tx_type'].isin(tx_type_filter)]
                                    if show_recurring:
                                                      filtered_df = filtered_df[filtered_df['is_recurring'] == True]

        # Display transactions
        display_df = filtered_df[['date', 'description', 'category', 'amount', 'balance']].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}")
        display_df['balance'] = display_df['balance'].apply(lambda x: f"${x:,.2f}")

        st.dataframe(display_df, use_container_width=True, height=400)

        st.markdown(f"**Showing {len(filtered_df)} of {len(df)} transactions**")

    with tab2:
                  st.markdown("### Daily Balance Trend")

        # Balance chart
                  balance_df = df.groupby('date').last().reset_index()
        st.line_chart(balance_df.set_index('date')['balance'])

        col1, col2 = st.columns(2)

        with col1:
                          st.markdown("### Revenue by Category")
                          revenue_by_cat = df[df['amount'] > 0].groupby('category')['amount'].sum()
                          st.bar_chart(revenue_by_cat)

        with col2:
                          st.markdown("### Expenses by Category")
                          expenses_by_cat = df[df['amount'] < 0].groupby('category')['amount'].sum().abs()
                          st.bar_chart(expenses_by_cat)

    with tab3:
                  st.markdown("### Risk Scorecard")

        col1, col2 = st.columns([1, 2])

        with col1:
                          st.markdown("#### Overall Score")
                          score_color = "🟢" if scores['overall'] >= 70 else "🟡" if scores['overall'] >= 50 else "🔴"
                          st.markdown(f"# {score_color} {scores['overall']}/100")

        with col2:
                          st.markdown("#### Score Breakdown")

            score_data = {
                                  'Category': ['Revenue Health', 'Debt Burden', 'Cash Flow', 'NSF/Overdraft'],
                                  'Score': [scores['revenue'], scores['debt_burden'], scores['cash_flow'], scores['nsf']],
                                  'Weight': ['30%', '25%', '25%', '20%']
            }
            st.dataframe(pd.DataFrame(score_data), use_container_width=True)

        st.markdown("---")
        st.markdown("### Score Factors")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
                          st.metric("Revenue Score", f"{scores['revenue']}/100")
                          st.caption(f"Avg Monthly: ${metrics['avg_monthly_revenue']:,.0f}")

        with col2:
                          st.metric("Debt Score", f"{scores['debt_burden']}/100")
                          debt_ratio = metrics['total_debt_payments'] / max(metrics['total_revenue'], 1) * 100
                          st.caption(f"Debt Ratio: {debt_ratio:.1f}%")

        with col3:
                          st.metric("Cash Flow Score", f"{scores['cash_flow']}/100")
                          st.caption(f"Avg Balance: ${metrics['avg_balance']:,.0f}")

        with col4:
                          st.metric("NSF Score", f"{scores['nsf']}/100")
                          st.caption(f"NSF Count: {metrics['nsf_count']}")

    with tab4:
                  st.markdown("### Debt Analysis")

        # MCA Detection
                  st.markdown("#### 🔴 MCA/Daily Debit Detection")
        mca_df = df[df['tx_type'] == 'mca_debt']

        if len(mca_df) > 0:
                          st.warning(f"⚠️ **{len(mca_df)} MCA-related transactions detected** totaling ${abs(mca_df['amount'].sum()):,.2f}")
                          st.dataframe(mca_df[['date', 'description', 'amount']], use_container_width=True)
else:
                  st.success("✅ No MCA payments detected")

        st.markdown("---")

        # Regular Debt
        st.markdown("#### 📊 Regular Debt Payments")
        debt_df = df[df['tx_type'] == 'regular_debt']

        if len(debt_df) > 0:
                          st.info(f"Found **{len(debt_df)} loan/debt payments** totaling ${abs(debt_df['amount'].sum()):,.2f}")

            # Group by description pattern
                          debt_summary = debt_df.groupby('category').agg({
                              'amount': ['sum', 'count', 'mean']
                          }).round(2)
                          debt_summary.columns = ['Total', 'Count', 'Avg Payment']
                          debt_summary['Total'] = debt_summary['Total'].abs()
                          debt_summary['Avg Payment'] = debt_summary['Avg Payment'].abs()
                          st.dataframe(debt_summary, use_container_width=True)
else:
                  st.info("No regular debt payments detected")

        st.markdown("---")

        # Recurring Transaction Detection
        st.markdown("#### 🔄 Recurring Transaction Patterns")
        recurring_df = df[df['is_recurring'] == True]
        recurring_summary = recurring_df.groupby('category').agg({
                          'amount': ['sum', 'count', 'mean']
        }).round(2)
        recurring_summary.columns = ['Total', 'Count', 'Avg Amount']
        st.dataframe(recurring_summary, use_container_width=True)

if __name__ == "__main__":
          main()
