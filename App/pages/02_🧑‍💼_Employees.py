# pages/02_Employees.py
"""
Streamlit page for managing Employee information (CRUD operations).
"""

import streamlit as st
import pandas as pd
from database import run_query, run_command
import datetime

st.set_page_config(page_title="Employee Management", layout="wide")
st.title("🧑‍💼 Employee Management")
st.write("View, Add, Edit, or Delete Employee records.")

# --- Helper Function to Get Stores for Dropdown ---
def get_store_options():
    stores = run_query("SELECT StoreID, StoreName FROM Stores ORDER BY StoreName;")
    if not stores.empty:
        return {f"{row['StoreName']} (ID: {row['StoreID']})": row['StoreID'] for index, row in stores.iterrows()}
    return {}

# --- Display Existing Employees ---
st.subheader("Existing Employees")
# Join with stores to show store name
query_emp = """
SELECT e.EmployeeID, e.FirstName, e.LastName, e.Position, e.HireDate, e.HourlyRate, s.StoreName
FROM Employees e
LEFT JOIN Stores s ON e.StoreID = s.StoreID
ORDER BY e.LastName, e.FirstName;
"""
df_employees = run_query(query_emp)
if not df_employees.empty:
    st.dataframe(df_employees, use_container_width=True, hide_index=True, column_config={
        "HourlyRate": st.column_config.NumberColumn(format="$%.2f")
    })
else:
    st.info("No employees found.")

st.divider()

# --- Add New Employee Form ---
st.subheader("Add New Employee")
store_options_add = get_store_options()
with st.form("add_employee_form", clear_on_submit=True):
    st.write("Enter details for the new employee:")
    add_fname = st.text_input("First Name*", max_chars=100)
    add_lname = st.text_input("Last Name*", max_chars=100)
    add_position = st.text_input("Position", max_chars=100)
    add_hire_date = st.date_input("Hire Date", value=datetime.date.today())
    add_rate = st.number_input("Hourly Rate", min_value=0.0, step=0.50, format="%.2f")
    # Dropdown for Store assignment
    add_store_display = st.selectbox("Assign to Store", options=store_options_add.keys(), index=None, placeholder="Select a store...")
    add_store_id = store_options_add.get(add_store_display) if add_store_display else None

    submitted_add = st.form_submit_button("Add Employee")
    if submitted_add:
        if not add_fname or not add_lname:
            st.warning("First Name and Last Name are required.")
        else:
            sql = """
            INSERT INTO Employees (FirstName, LastName, Position, HireDate, HourlyRate, StoreID)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            params = (add_fname, add_lname, add_position, add_hire_date, add_rate, add_store_id)
            success, _ = run_command(sql, params)
            if success:
                st.success(f"Employee '{add_fname} {add_lname}' added successfully!")

st.divider()

# --- Edit Existing Employee ---
st.subheader("Edit Existing Employee")
employee_list = run_query("SELECT EmployeeID, FirstName, LastName FROM Employees ORDER BY LastName, FirstName;")
if not employee_list.empty:
    emp_options = {f"{row['LastName']}, {row['FirstName']} (ID: {row['EmployeeID']})": row['EmployeeID'] for index, row in employee_list.iterrows()}
    selected_emp_display = st.selectbox("Select Employee to Edit", options=emp_options.keys())

    if selected_emp_display:
        selected_emp_id = emp_options[selected_emp_display]
        current_emp_data = run_query("SELECT * FROM Employees WHERE EmployeeID = %s;", params=(selected_emp_id,))

        if not current_emp_data.empty:
            emp = current_emp_data.iloc[0]
            store_options_edit = get_store_options()
            # Find the display key for the current StoreID
            current_store_key = None
            for key, val in store_options_edit.items():
                if val == emp['StoreID']:
                    current_store_key = key
                    break
            # Handle if current store doesn't exist or employee not assigned
            current_store_index = list(store_options_edit.keys()).index(current_store_key) if current_store_key else None


            with st.form(f"edit_employee_{selected_emp_id}"):
                st.write(f"Editing: {emp['FirstName']} {emp['LastName']}")
                edit_fname = st.text_input("First Name*", value=emp['FirstName'], max_chars=100)
                edit_lname = st.text_input("Last Name*", value=emp['LastName'], max_chars=100)
                edit_position = st.text_input("Position", value=emp['Position'], max_chars=100)
                # Ensure date is in correct format for date_input
                edit_hire_date_val = emp['HireDate'] if isinstance(emp['HireDate'], datetime.date) else datetime.date.today()
                edit_hire_date = st.date_input("Hire Date", value=edit_hire_date_val)
                edit_rate = st.number_input("Hourly Rate", value=float(emp['HourlyRate'] if emp['HourlyRate'] else 0.0), min_value=0.0, step=0.50, format="%.2f")
                edit_store_display = st.selectbox("Assign to Store",
                                                  options=store_options_edit.keys(),
                                                  index=current_store_index,
                                                  placeholder="Select a store..." )
                edit_store_id = store_options_edit.get(edit_store_display) if edit_store_display else None


                submitted_edit = st.form_submit_button("Update Employee")
                if submitted_edit:
                    if not edit_fname or not edit_lname:
                        st.warning("First Name and Last Name are required.")
                    else:
                        sql_update = """
                            UPDATE Employees
                            SET FirstName=%s, LastName=%s, Position=%s, HireDate=%s, HourlyRate=%s, StoreID=%s
                            WHERE EmployeeID=%s;
                        """
                        params_update = (edit_fname, edit_lname, edit_position, edit_hire_date, edit_rate, edit_store_id, selected_emp_id)
                        success, _ = run_command(sql_update, params_update)
                        if success:
                            st.success(f"Employee '{edit_fname} {edit_lname}' updated successfully!")
                            st.rerun()
else:
    st.info("No employees available to edit.")

st.divider()

# --- Delete Existing Employee ---
st.subheader("Delete Existing Employee")
if not employee_list.empty:
    emp_options_del = {f"{row['LastName']}, {row['FirstName']} (ID: {row['EmployeeID']})": row['EmployeeID'] for index, row in employee_list.iterrows()}
    selected_emp_display_del = st.selectbox("Select Employee to Delete", options=emp_options_del.keys(), key="delete_emp_select")

    if selected_emp_display_del:
        selected_emp_id_del = emp_options_del[selected_emp_display_del]
        emp_name_del = selected_emp_display_del.split(" (ID:")[0]

        if st.button(f"Confirm Delete Employee: {emp_name_del}"):
            # Check for related orders (FK is RESTRICT)
            orders_exist = run_query("SELECT COUNT(*) as count FROM Orders WHERE EmployeeID = %s;", params=(selected_emp_id_del,))
            if orders_exist.iloc[0]['count'] > 0:
                st.error(f"Cannot delete employee. {orders_exist.iloc[0]['count']} order(s) reference this employee. (Deletion restricted by database constraint). Please reassign or delete orders first.")
            else:
                sql_delete = "DELETE FROM Employees WHERE EmployeeID = %s;"
                params_delete = (selected_emp_id_del,)
                success, _ = run_command(sql_delete, params_delete)
                if success:
                    st.success(f"Employee '{emp_name_del}' deleted successfully!")
                    st.rerun()
else:
    st.info("No employees available to delete.")