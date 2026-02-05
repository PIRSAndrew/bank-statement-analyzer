# Bank Statement Analyzer - Phase 1 Setup Guide

## What's New (Phase 1)

✅ **Database Persistence** - Statements, transactions, and learned patterns now persist  
✅ **User Authentication** - Secure login/signup with Supabase  
✅ **Multi-User Support** - Each user has isolated data  
✅ **Statement History** - View all previously uploaded statements  
✅ **Pattern Persistence** - Learned patterns survive across sessions  

## Architecture

```
User Login (Supabase Auth)
    ↓
SQLAlchemy ORM Models
    ↓
PostgreSQL Database (Supabase)
    ↓
Persistent Data Storage
```

## Files Added/Changed

| File | Purpose |
|------|---------|
| `database.py` | SQLAlchemy models and CRUD functions |
| `auth.py` | Supabase authentication module |
| `streamlit_app_v2.py` | Refactored main app with persistence |
| `SETUP_PHASE_1.md` | This guide |

**Note:** `streamlit_app.py` (original) is kept for reference. To activate Phase 1, update your `streamlit_app.py` to match `streamlit_app_v2.py` or replace it.

---

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. 2. Click "Start your project"
   3. 3. Sign up or log in
      4. 4. Create a new project:
         5.    - **Project Name:** `bank-analyzer`
               -    - **Database Password:** Save this securely
                    -    - **Region:** Choose closest to you
                         - 5. Wait for project to initialize (~2 minutes)
                          
                           6. ---
                          
                           7. ## Step 2: Get Connection Credentials
                          
                           8. 1. Go to **Settings → Database** in your Supabase dashboard
                              2. 2. Copy these values:
                                 3.    - **Project URL** (PostgreSQL Connection String)
                                       -    - **Project API Key** (anon/public key)
                                        
                                            - You'll also need:
                                            - - **Supabase URL** - found in Settings → API
                                              - - **Supabase Key** - found in Settings → API (anon key)
                                               
                                                - ---

                                                ## Step 3: Update Environment Variables

                                                ### For Local Development:

                                                Create a `.env` file in your project root:

                                                ```bash
                                                # Database Connection
                                                DATABASE_URL="postgresql://postgres:[PASSWORD]@[PROJECT-ID].supabase.co:5432/postgres"

                                                # Supabase Auth
                                                SUPABASE_URL="https://[PROJECT-ID].supabase.co"
                                                SUPABASE_KEY="[YOUR-ANON-KEY]"
                                                ```

                                                Replace:
                                                - `[PASSWORD]` - The password you set during project creation
                                                - - `[PROJECT-ID]` - Your Supabase project ID
                                                  - - `[YOUR-ANON-KEY]` - Your anon/public API key
                                                   
                                                    - ### For Streamlit Cloud:
                                                   
                                                    - 1. Go to your app settings: https://share.streamlit.io/admin/apps
                                                      2. 2. Click your app → **Settings**
                                                         3. 3. Add secrets under "Secrets":
                                                           
                                                            4. ```toml
                                                               DATABASE_URL = "postgresql://postgres:[PASSWORD]@[PROJECT-ID].supabase.co:5432/postgres"
                                                               SUPABASE_URL = "https://[PROJECT-ID].supabase.co"
                                                               SUPABASE_KEY = "[YOUR-ANON-KEY]"
                                                               ```

                                                               ---

                                                               ## Step 4: Update Dependencies

                                                               Update your `requirements.txt`:

                                                               ```txt
                                                               streamlit
                                                               pandas
                                                               pdfplumber
                                                               sqlalchemy
                                                               psycopg2-binary
                                                               supabase
                                                               python-dotenv
                                                               ```

                                                               Then install:
                                                               ```bash
                                                               pip install -r requirements.txt
                                                               ```

                                                               ---

                                                               ## Step 5: Initialize Database Tables

                                                               Run this command to create tables:

                                                               ```python
                                                               from database import init_db
                                                               init_db()
                                                               ```

                                                               Or simply run the app and let it auto-create tables on first run.

                                                               ---

                                                               ## Step 6: Update Your Streamlit Config

                                                               Update `.streamlit/config.toml` (create if doesn't exist):

                                                               ```toml
                                                               [client]
                                                               showErrorDetails = true

                                                               [logger]
                                                               level = "error"

                                                               [theme]
                                                               primaryColor = "#1f77b4"
                                                               backgroundColor = "#ffffff"
                                                               secondaryBackgroundColor = "#f0f2f6"
                                                               textColor = "#262730"
                                                               font = "sans serif"
                                                               ```

                                                               ---

                                                               ## Step 7: Deploy to Streamlit Cloud

                                                               1. Push your changes to GitHub
                                                               2. 2. Go to [share.streamlit.io](https://share.streamlit.io)
                                                                  3. 3. Click "New app"
                                                                     4. 4. Select your repository
                                                                        5. 5. **IMPORTANT:** Add secrets (see Step 3 above)
                                                                           6. 6. Deploy!
                                                                             
                                                                              7. ---
                                                                             
                                                                              8. ## Testing Phase 1
                                                                             
                                                                              9. ### Test Login/Signup:
                                                                              10. 1. Go to your Streamlit app
                                                                                  2. 2. Click "Sign Up" tab
                                                                                     3. 3. Create a test account: `test@example.com` / `test123456`
                                                                                        4. 4. You should be logged in and see the main app
                                                                                          
                                                                                           5. ### Test Persistence:
                                                                                           6. 1. Upload a sample bank statement PDF
                                                                                              2. 2. Refresh the page
                                                                                                 3. 3. You should see "Recent Statements" with your uploaded file
                                                                                                    4. 4. The data should still be there!
                                                                                                      
                                                                                                       5. ### Test Pattern Learning:
                                                                                                       6. 1. In the sidebar, enter a pattern: `"DAILY ACH"`
                                                                                                          2. 2. Select category: `MCA_DEBT`
                                                                                                             3. 3. Click "Add Pattern"
                                                                                                                4. 4. Refresh the page
                                                                                                                   5. 5. Pattern should still be there in the learned patterns list
                                                                                                                     
                                                                                                                      6. ---
                                                                                                                     
                                                                                                                      7. ## Troubleshooting
                                                                                                                     
                                                                                                                      8. ### "Missing Supabase configuration"
                                                                                                                      9. - Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
                                                                                                                         - - Or check Streamlit Cloud secrets
                                                                                                                          
                                                                                                                           - ### "Connection refused" on DATABASE_URL
                                                                                                                           - - Verify PostgreSQL connection string is correct
                                                                                                                             - - Check database password
                                                                                                                               - - Ensure Supabase IP whitelist includes your server
                                                                                                                                
                                                                                                                                 - ### "Auth failed"
                                                                                                                                 - - Verify `SUPABASE_KEY` is the **anon key** (not secret key)
                                                                                                                                   - - Check project hasn't been deleted
                                                                                                                                    
                                                                                                                                     - ### Tables not created
                                                                                                                                     - - Run `init_db()` manually
                                                                                                                                       - - Check database permissions in Supabase
                                                                                                                                        
                                                                                                                                         - ---
                                                                                                                                         
                                                                                                                                         ## What's Next (Phase 2)
                                                                                                                                         
                                                                                                                                         - Month-over-month analysis
                                                                                                                                         - - Spending trends and dashboards
                                                                                                                                           - - Email reports
                                                                                                                                             - - Budget alerts
                                                                                                                                               - - Data export (CSV, PDF)
                                                                                                                                                
                                                                                                                                                 - ---
                                                                                                                                                 
                                                                                                                                                 ## Architecture Details
                                                                                                                                                 
                                                                                                                                                 ### Database Schema
                                                                                                                                                 
                                                                                                                                                 ```
                                                                                                                                                 users
                                                                                                                                                 ├── id (UUID from Supabase Auth)
                                                                                                                                                 ├── email
                                                                                                                                                 ├── created_at
                                                                                                                                                 └── updated_at

                                                                                                                                                 bank_statements
                                                                                                                                                 ├── id (Primary Key)
                                                                                                                                                 ├── user_id (Foreign Key → users)
                                                                                                                                                 ├── filename
                                                                                                                                                 ├── upload_date
                                                                                                                                                 ├── statement_month
                                                                                                                                                 ├── total_transactions
                                                                                                                                                 ├── total_revenue
                                                                                                                                                 ├── total_expenses
                                                                                                                                                 ├── net_cash_flow
                                                                                                                                                 ├── health_score
                                                                                                                                                 └── raw_data (JSON)

                                                                                                                                                 transactions
                                                                                                                                                 ├── id (Primary Key)
                                                                                                                                                 ├── statement_id (Foreign Key → bank_statements)
                                                                                                                                                 ├── date
                                                                                                                                                 ├── description
                                                                                                                                                 ├── amount
                                                                                                                                                 ├── category
                                                                                                                                                 ├── category_confidence
                                                                                                                                                 ├── user_corrected
                                                                                                                                                 └── created_at

                                                                                                                                                 learned_patterns
                                                                                                                                                 ├── id (Primary Key)
                                                                                                                                                 ├── user_id (Foreign Key → users)
                                                                                                                                                 ├── pattern
                                                                                                                                                 ├── category
                                                                                                                                                 ├── times_used
                                                                                                                                                 ├── confidence
                                                                                                                                                 └── created_at
                                                                                                                                                 ```
                                                                                                                                                 
                                                                                                                                                 ### Authentication Flow
                                                                                                                                                 
                                                                                                                                                 ```
                                                                                                                                                 User enters email/password
                                                                                                                                                     ↓
                                                                                                                                                 Supabase Auth validates
                                                                                                                                                     ↓
                                                                                                                                                 User ID saved to session
                                                                                                                                                     ↓
                                                                                                                                                 User created in database (if new)
                                                                                                                                                     ↓
                                                                                                                                                 User can access their data
                                                                                                                                                 ```
                                                                                                                                                 
                                                                                                                                                 ---
                                                                                                                                                 
                                                                                                                                                 ## Key Code Changes
                                                                                                                                                 
                                                                                                                                                 ### Before (v1):
                                                                                                                                                 ```python
                                                                                                                                                 if 'learned_patterns' not in st.session_state:
                                                                                                                                                     st.session_state.learned_patterns = {}
                                                                                                                                                 # Data lost on refresh ❌
                                                                                                                                                 ```
                                                                                                                                                 
                                                                                                                                                 ### After (v2):
                                                                                                                                                 ```python
                                                                                                                                                 db = SessionLocal()
                                                                                                                                                 patterns = get_user_patterns(db, st.session_state.user_id)
                                                                                                                                                 save_learned_pattern(db, user_id, pattern, category)
                                                                                                                                                 # Data persists forever ✅
                                                                                                                                                 ```
                                                                                                                                                 
                                                                                                                                                 ---
                                                                                                                                                 
                                                                                                                                                 ## Frequently Asked Questions
                                                                                                                                                 
                                                                                                                                                 **Q: Do I need a Supabase account?**
                                                                                                                                                 A: Yes, it's free tier is generous (500MB database, unlimited API calls).
                                                                                                                                                 
                                                                                                                                                 **Q: How much will this cost?**
                                                                                                                                                 A: For personal use, it's free! Supabase free tier covers thousands of users.
                                                                                                                                                 
                                                                                                                                                 **Q: Can I use a different database?**
                                                                                                                                                 A: Yes! SQLAlchemy supports MySQL, PostgreSQL, SQLite, etc. Change `DATABASE_URL`.
                                                                                                                                                 
                                                                                                                                                 **Q: How do I backup my data?**
                                                                                                                                                 A: Supabase has automated backups. You can also export via their dashboard.
                                                                                                                                                 
                                                                                                                                                 **Q: When will Phase 2 be ready?**
                                                                                                                                                 A: Currently in development. Estimated 1-2 weeks for Phase 2.
                                                                                                                                                 
                                                                                                                                                 ---
                                                                                                                                                 
                                                                                                                                                 ## Support
                                                                                                                                                 
                                                                                                                                                 If you encounter issues:
                                                                                                                                                 1. Check the troubleshooting section above
                                                                                                                                                 2. 2. Review Supabase docs: https://supabase.com/docs
                                                                                                                                                    3. 3. Check SQLAlchemy docs: https://docs.sqlalchemy.org
                                                                                                                                                       4. 4. Open an issue on GitHub
                                                                                                                                                         
                                                                                                                                                          5. Good luck! 🚀
