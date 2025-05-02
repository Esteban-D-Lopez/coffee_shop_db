# pages/03_Customers.py
"""
Streamlit page for managing Customer information (CRUD operations).
Uses the sp_AddCustomer stored procedure for inserts.
"""

import streamlit as st
import pandas as pd
from database import run_query, run_command, call_sp_add_customer # Import specific procedure call
import datetime

st.set_page_config(page_title="Customer Management", layout="wide")
st.title("❤️ Customer Management")
st.write("View, Add, Edit, or Delete Customer records and view loyalty points.")

# --- Display Existing Customers ---
st.subheader("Existing Customers")
# Using the view to show summary data might be nice here too
# df_customers = run_query("SELECT * FROM vw_CustomerOrderSummary ORDER BY LastName, FirstName;")
df_customers = run_query("SELECT CustomerID, FirstName, LastName, Email, PhoneNumber, JoinDate, LoyaltyPoints FROM Customers ORDER BY LastName, FirstName;")

if not df_customers.empty:
    st.dataframe(df_customers, use_container_width=True, hide_index=True)
else:
    st.info("No customers found.")

st.divider()

# --- Add New Customer Form ---
st.subheader("Add New Customer")
with st.form("add_customer_form", clear_on_submit=True):
    st.write("Enter details for the new customer:")
    add_fname = st.text_input("First Name*", max_chars=100)
    add_lname = st.text_input("Last Name*", max_chars=100)
    add_email = st.text_input("Email*", max_chars=255)
    add_phone = st.text_input("Phone Number", max_chars=50, placeholder="(Optional)")

    submitted_add = st.form_submit_button("Add Customer")
    if submitted_add:
        if not add_fname or not add_lname or not add_email:
            st.warning("First Name, Last Name, and Email are required.")
        # Basic email format check (not perfect)
        elif "@" not in add_email or "." not in add_email.split("@")[-1]:
             st.warning("Please enter a valid email address.")
        else:
            # Use the specific procedure call function
            # Handle optional phone number (pass None if empty)
            phone_to_pass = add_phone if add_phone else None
            success = call_sp_add_customer(add_fname, add_lname, add_email, phone_to_pass)
            if success:
                st.success(f"Customer '{add_fname} {add_lname}' added successfully!")
            # Error message is handled within run_command/call_sp... if SIGNAL is raised

st.divider()

# --- Edit Existing Customer ---
st.subheader("Edit Existing Customer")
customer_list = run_query("SELECT CustomerID, FirstName, LastName, Email FROM Customers ORDER BY LastName, FirstName;")
if not customer_list.empty:
    cust_options = {f"{row['LastName']}, {row['FirstName']} ({row['Email']})": row['CustomerID'] for index, row in customer_list.iterrows()}
    selected_cust_display = st.selectbox("Select Customer to Edit", options=cust_options.keys())

    if selected_cust_display:
        selected_cust_id = cust_options[selected_cust_display]
        current_cust_data = run_query("SELECT * FROM Customers WHERE CustomerID = %s;", params=(selected_cust_id,))

        if not current_cust_data.empty:
            cust = current_cust_data.iloc[0]

            with st.form(f"edit_customer_{selected_cust_id}"):
                st.write(f"Editing: {cust['FirstName']} {cust['LastName']}")
                edit_fname = st.text_input("First Name*", value=cust['FirstName'], max_chars=100)
                edit_lname = st.text_input("Last Name*", value=cust['LastName'], max_chars=100)
                edit_email = st.text_input("Email*", value=cust['Email'], max_chars=255)
                edit_phone = st.text_input("Phone Number", value=cust['PhoneNumber'] if cust['PhoneNumber'] else "", max_chars=50)
                # Display loyalty points, but maybe don't allow direct editing here
                st.text_input("Loyalty Points", value=str(cust['LoyaltyPoints']), disabled=True)
                # Join Date might also be read-only
                st.date_input("Join Date", value=cust['JoinDate'], disabled=True)


                submitted_edit = st.form_submit_button("Update Customer")
                if submitted_edit:
                    if not edit_fname or not edit_lname or not edit_email:
                        st.warning("First Name, Last Name, and Email are required.")
                    elif "@" not in edit_email or "." not in edit_email.split("@")[-1]:
                         st.warning("Please enter a valid email address.")
                    else:
                        phone_to_update = edit_phone if edit_phone else None
                        sql_update = """
                            UPDATE Customers
                            SET FirstName=%s, LastName=%s, Email=%s, PhoneNumber=%s
                            WHERE CustomerID=%s;
                        """
                        # Note: Not updating JoinDate or LoyaltyPoints via this form
                        params_update = (edit_fname, edit_lname, edit_email, phone_to_update, selected_cust_id)
                        success, _ = run_command(sql_update, params_update)
                        if success:
                            st.success(f"Customer '{edit_fname} {edit_lname}' updated successfully!")
                            st.rerun()
else:
    st.info("No customers available to edit.")

st.divider()

# --- Delete Existing Customer ---
st.subheader("Delete Existing Customer")
if not customer_list.empty:
    cust_options_del = {f"{row['LastName']}, {row['FirstName']} ({row['Email']})": row['CustomerID'] for index, row in customer_list.iterrows()}
    selected_cust_display_del = st.selectbox("Select Customer to Delete", options=cust_options_del.keys(), key="delete_cust_select")

    if selected_cust_display_del:
        selected_cust_id_del = cust_options_del[selected_cust_display_del]
        cust_name_del = selected_cust_display_del.split(" (")[0] # Get name part

        if st.button(f"Confirm Delete Customer: {cust_name_del}"):
            # Note: ON DELETE SET NULL for Orders means associated orders will remain but point to NULL CustomerID
            st.info("Deleting a customer will set their ID to NULL in past orders.")
            sql_delete = "DELETE FROM Customers WHERE CustomerID = %s;"
            params_delete = (selected_cust_id_del,)
            success, _ = run_command(sql_delete, params_delete)
            if success:
                st.success(f"Customer '{cust_name_del}' deleted successfully!")
                st.rerun()
else:
    st.info("No customers available to delete.")