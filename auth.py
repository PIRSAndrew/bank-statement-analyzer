"""
Supabase authentication integration for Bank Statement Analyzer.
Handles user login, signup, and session management.
"""

import streamlit as st
from supabase import create_client, Client
import os
from database import SessionLocal, get_user, create_user, user_exists

# Initialize Supabase client - check st.secrets first, then env vars
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Missing Supabase configuration. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def init_auth_state():
    """Initialize authentication state in session"""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False


def login(email, password):
    """Login user with email and password"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            st.session_state.user = response.user
            st.session_state.user_id = response.user.id
            st.session_state.email = response.user.email
            st.session_state.authenticated = True

            # Ensure user exists in database
            db = SessionLocal()
            if not user_exists(db, response.user.id):
                create_user(db, response.user.id, response.user.email)
            db.close()

            return True, "✅ Login successful!"
        return False, "❌ Login failed"

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return False, "❌ Invalid email or password"
        return False, f"❌ Login failed: {error_msg}"


def signup(email, password, confirm_password):
    """Register a new user"""
    if password != confirm_password:
        return False, "❌ Passwords do not match"

    if len(password) < 6:
        return False, "❌ Password must be at least 6 characters"

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if response.user:
            st.session_state.user = response.user
            st.session_state.user_id = response.user.id
            st.session_state.email = response.user.email
            st.session_state.authenticated = True

            # Create user in database
            db = SessionLocal()
            create_user(db, response.user.id, response.user.email)
            db.close()

            return True, "✅ Account created successfully!"

    except Exception as e:
        error_msg = str(e)
        if "already" in error_msg.lower():
            return False, "❌ Email already registered"
        return False, f"❌ Signup failed: {error_msg}"

    return False, "❌ Signup failed"


def logout():
    """Logout current user"""
    try:
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.email = None
        st.session_state.authenticated = False
        return True, "✅ Logged out successfully"
    except Exception as e:
        return False, f"❌ Logout failed: {str(e)}"


def get_current_user():
    """Get current authenticated user"""
    if st.session_state.authenticated and st.session_state.user_id:
        db = SessionLocal()
        user = get_user(db, st.session_state.user_id)
        db.close()
        return user
    return None


def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def require_auth():
    """Decorator-like function to require authentication"""
    if not is_authenticated():
        render_auth_page()
        st.stop()


def render_auth_page():
    """Render login/signup page"""
    st.title("🏦 Bank Statement Analyzer")
    st.subheader("Please log in or create an account")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Log In", key="login_btn", use_container_width=True):
            if login_email and login_password:
                success, message = login(login_email, login_password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("❌ Please enter email and password")

    with tab2:
        st.subheader("Create Account")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Sign Up", key="signup_btn", use_container_width=True):
            if signup_email and signup_password and signup_password_confirm:
                success, message = signup(signup_email, signup_password, signup_password_confirm)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("❌ Please fill in all fields")

    st.markdown("---")
    st.markdown("""
        **Demo Credentials:**
        - Email: `demo@example.com`
        - Password: `demo123456`

        or create your own account above
        """)


def render_user_menu():
    """Render user menu in sidebar"""
    if is_authenticated():
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **{st.session_state.email}**")

        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
