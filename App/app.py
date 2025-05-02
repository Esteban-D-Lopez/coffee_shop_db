# app.py (Main App / Home Page)

import streamlit as st
import datetime
from database import run_query # Import the necessary DB function

# --- Page Configuration ---
st.set_page_config(
    page_title="Coffee Shop Mgmt", # Shorter title for browser tab
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Main Application Title ---
st.title("☕ Coffee Shop Management System")

# --- Home Page Content ---
# This content runs when the app first loads or 'app.py' is selected implicitly
st.header("Dashboard / Home")
st.write("Welcome! Select a management area from the sidebar.")
st.write("Current Time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

st.divider()
st.write("Application allows managing Stores, Employees, Customers, Products, Promotions, Orders, and viewing Reports.")

# --- Footer Placeholder in Sidebar ---
st.sidebar.markdown("---")
st.sidebar.info(f"Coffee Shop App | {datetime.date.today().year}")