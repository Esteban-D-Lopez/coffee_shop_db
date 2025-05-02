# database.py
"""
Handles database connection and execution of queries/commands.
Uses PyMySQL to connect to the MySQL database.
"""

import streamlit as st
import pymysql
import pandas as pd

# --- Database Configuration ---
# Store database credentials securely (consider environment variables for production)
DB_CONFIG = {
    'host': "127.0.0.1",       # Or 'localhost'
    'port': 3306,             # Default MySQL port
    'user': "root",           # Local MySQL username if not root
    'password': "password", # password
    'database': "coffee_shop",
    'cursorclass': pymysql.cursors.DictCursor # Fetch results as dictionaries
}

# --- Connection Function ---
@st.cache_resource(show_spinner="Connecting to database...") # Cache the connection
def get_connection():
    """Establishes and returns a database connection."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.MySQLError as e:
        st.error(f"Error connecting to MySQL database: {e}")
        # Stop the app if DB connection fails
        # Returning None and checking might be better in some cases
        st.stop()
    except Exception as ex:
        st.error(f"An unexpected error occurred during connection: {ex}")
        st.stop()


# --- Query Function ---
# @st.cache_data(ttl=60, show_spinner="Running query...") # Optional: Cache query results
def run_query(query, params=None):
    """
    Executes a SELECT query and returns the results as a Pandas DataFrame.
    Handles potential database errors.
    """
    conn = get_connection()
    try:
        # Use context manager for cursor safety
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            if results:
                column_names = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(results, columns=column_names)
            else:
                # Return empty DataFrame with columns if no results
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                df = pd.DataFrame(columns=column_names)
            return df
    except pymysql.MySQLError as e:
        st.error(f"Database Query Error: {e}")
    except Exception as ex:
        st.error(f"An error occurred during query execution: {ex}")
    return pd.DataFrame() # Return empty DataFrame on error


# --- Command Function ---
def run_command(sql, params=None, fetch_output=False):
    """
    Executes a database command (INSERT, UPDATE, DELETE, CALL).
    Handles transactions and potential errors.
    Can optionally fetch output parameters from stored procedures.
    Returns success status (True/False) and optionally fetched output.
    """
    conn = get_connection()
    output = None
    success = False
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)

            # Fetch output parameters if requested (specific to CALL statements)
            if fetch_output and sql.strip().upper().startswith("CALL"):
                 # Assumes output params are selected by the procedure after the call
                 # This might need adjustment based on how procedures return output
                 cursor.execute("SELECT @_proc_output AS output_param;") # Example convention
                 output_result = cursor.fetchone()
                 if output_result:
                     output = output_result.get('output_param') # Assumes DictCursor

            conn.commit() # Commit changes
            success = True
            st.toast("Command executed successfully!", icon="✔️")
            # Clear relevant caches if modifications were made
            # st.cache_data.clear() # Simple approach
            # Consider more granular cache invalidation if performance is critical
    except pymysql.MySQLError as e:
        conn.rollback() # Rollback changes on error
        st.error(f"Database Command Error: {e}")
    except Exception as ex:
        conn.rollback()
        st.error(f"An error occurred during command execution: {ex}")
    finally:
        # Note: The connection is cached and shouldn't be closed here
        pass

    return success, output


# --- Stored Procedure Call Functions (Examples) ---
def call_sp_add_customer(first_name, last_name, email, phone):
    """Calls the sp_AddCustomer stored procedure."""
    sql = "CALL sp_AddCustomer(%s, %s, %s, %s, @new_id);"
    params = (first_name, last_name, email, phone)
    success, _ = run_command(sql, params) # Ignore output param for now
    return success

def call_sp_process_order(customer_id, employee_id, store_id, items_string, points_redeemed):
    """Calls the sp_ProcessOrder stored procedure."""
    # Convention: Procedure sets session variable @_proc_output with the new OrderID
    sql = "CALL sp_ProcessOrder(%s, %s, %s, %s, %s, @new_ord_id);"
    params = (customer_id, employee_id, store_id, items_string, points_redeemed)
    
    success, _ = run_command(sql, params)
    new_order_id = None
    if success:
         df_new_id = run_query("SELECT @new_ord_id AS NewOrderID;")
         if not df_new_id.empty:
              new_order_id = df_new_id.iloc[0]['NewOrderID']
    return success, new_order_id