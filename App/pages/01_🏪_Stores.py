# pages/01_Stores.py
"""
Streamlit page for managing Store information (CRUD operations).
"""

import streamlit as st
import pandas as pd
from database import run_query, run_command

# --- Page Configuration ---
st.set_page_config(page_title="Store Management", layout="wide")
st.title("🏪 Store Management")
st.write("View, Add, Edit, or Delete Store locations.")

# --- Display Existing Stores ---
st.subheader("Existing Stores")
df_stores = run_query("SELECT * FROM Stores ORDER BY StoreName;")
if not df_stores.empty:
    st.dataframe(df_stores, use_container_width=True, hide_index=True)
else:
    st.info("No stores found in the database.")

st.divider()

# --- Add New Store Form ---
st.subheader("Add New Store")
with st.form("add_store_form", clear_on_submit=True):
    st.write("Enter details for the new store:")
    new_name = st.text_input("Store Name*", max_chars=150)
    new_address = st.text_input("Address", max_chars=255)
    new_city = st.text_input("City", max_chars=100)
    new_state = st.text_input("State", max_chars=50)
    new_zip = st.text_input("Zip Code", max_chars=20)

    submitted_add = st.form_submit_button("Add Store")
    if submitted_add:
        if not new_name:
            st.warning("Store Name is required.")
        else:
            sql = "INSERT INTO Stores (StoreName, Address, City, State, ZipCode) VALUES (%s, %s, %s, %s, %s);"
            params = (new_name, new_address, new_city, new_state, new_zip)
            success, _ = run_command(sql, params)
            if success:
                st.success(f"Store '{new_name}' added successfully!")
                # No explicit rerun needed due to form submission behavior
            # Error message is handled by run_command

st.divider()

# --- Edit Existing Store ---
st.subheader("Edit Existing Store")
# Get list of stores for selection
store_list = run_query("SELECT StoreID, StoreName FROM Stores ORDER BY StoreName;")
if not store_list.empty:
    # Create a mapping from display name to ID
    store_options = {f"{row['StoreName']} (ID: {row['StoreID']})": row['StoreID'] for index, row in store_list.iterrows()}
    selected_store_display = st.selectbox("Select Store to Edit", options=store_options.keys())

    if selected_store_display:
        selected_store_id = store_options[selected_store_display]

        # Fetch current data for the selected store
        current_store_data = run_query("SELECT * FROM Stores WHERE StoreID = %s;", params=(selected_store_id,))

        if not current_store_data.empty:
            store = current_store_data.iloc[0] # Get the first (only) row

            with st.form(f"edit_store_{selected_store_id}"):
                st.write(f"Editing: {store['StoreName']}")
                edit_name = st.text_input("Store Name*", value=store['StoreName'], max_chars=150)
                edit_address = st.text_input("Address", value=store['Address'], max_chars=255)
                edit_city = st.text_input("City", value=store['City'], max_chars=100)
                edit_state = st.text_input("State", value=store['State'], max_chars=50)
                edit_zip = st.text_input("Zip Code", value=store['ZipCode'], max_chars=20)

                submitted_edit = st.form_submit_button("Update Store")
                if submitted_edit:
                    if not edit_name:
                        st.warning("Store Name is required.")
                    else:
                        sql_update = """
                            UPDATE Stores
                            SET StoreName=%s, Address=%s, City=%s, State=%s, ZipCode=%s
                            WHERE StoreID=%s;
                        """
                        params_update = (edit_name, edit_address, edit_city, edit_state, edit_zip, selected_store_id)
                        success, _ = run_command(sql_update, params_update)
                        if success:
                            st.success(f"Store '{edit_name}' updated successfully!")
                            st.rerun() # Rerun to refresh the selectbox and table
                        # Error handled by run_command
        else:
            st.error("Could not fetch store data.")
else:
    st.info("No stores available to edit.")

st.divider()

# --- Delete Existing Store ---
st.subheader("Delete Existing Store")
# Re-fetch or reuse store_list for consistency
if not store_list.empty:
    store_options_del = {f"{row['StoreName']} (ID: {row['StoreID']})": row['StoreID'] for index, row in store_list.iterrows()}
    selected_store_display_del = st.selectbox("Select Store to Delete", options=store_options_del.keys(), key="delete_store_select")

    if selected_store_display_del:
        selected_store_id_del = store_options_del[selected_store_display_del]
        store_name_del = selected_store_display_del.split(" (ID:")[0] # Get name for confirmation

        if st.button(f"Confirm Delete Store: {store_name_del}"):
            try:
                # Check related records (optional but good practice, FKs might handle this)
                # Example: Check if employees are assigned to this store
                employees_assigned = run_query("SELECT COUNT(*) as count FROM Employees WHERE StoreID = %s;", params=(selected_store_id_del,))
                if employees_assigned.iloc[0]['count'] > 0:
                     st.warning(f"Cannot delete store. {employees_assigned.iloc[0]['count']} employee(s) are assigned (Their StoreID will be set to NULL due to ON DELETE SET NULL). Proceed with caution or reassign first.")
                     # Depending on strictness, you might prevent deletion entirely here.

                # Check if orders reference this store
                orders_exist = run_query("SELECT COUNT(*) as count FROM Orders WHERE StoreID = %s;", params=(selected_store_id_del,))
                if orders_exist.iloc[0]['count'] > 0:
                     st.error(f"Cannot delete store. {orders_exist.iloc[0]['count']} order(s) reference this store. (Deletion restricted by database constraint). Please reassign or delete orders first.")
                else:
                    # Proceed with deletion if no restricting orders exist
                    sql_delete = "DELETE FROM Stores WHERE StoreID = %s;"
                    params_delete = (selected_store_id_del,)
                    success, _ = run_command(sql_delete, params_delete)
                    if success:
                        st.success(f"Store '{store_name_del}' deleted successfully!")
                        st.rerun() # Refresh page
                    # Error handled by run_command

            except Exception as e:
                st.error(f"An error occurred during deletion: {e}")
else:
    st.info("No stores available to delete.")