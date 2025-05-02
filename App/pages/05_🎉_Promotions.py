# pages/05_Promotions.py
"""
Streamlit page for managing Promotion information (CRUD operations).
"""

import streamlit as st
import pandas as pd
from database import run_query, run_command
import datetime

st.set_page_config(page_title="Promotion Management", layout="wide")
st.title("🎉 Promotion Management")
st.write("View, Add, Edit, or Delete Promotions.")

# --- Display Existing Promotions ---
st.subheader("Active & Past Promotions")
df_promotions = run_query("SELECT * FROM Promotions ORDER BY EndDate DESC, StartDate DESC;")
if not df_promotions.empty:
    st.dataframe(df_promotions, use_container_width=True, hide_index=True, column_config={
        "DiscountValue": st.column_config.NumberColumn(format="%.2f"),
        "StartDate": st.column_config.DateColumn(format="YYYY-MM-DD"),
        "EndDate": st.column_config.DateColumn(format="YYYY-MM-DD")
    })
else:
    st.info("No promotions found.")

st.divider()

# --- Add New Promotion Form ---
st.subheader("Add New Promotion")
with st.form("add_promo_form", clear_on_submit=True):
    st.write("Enter details for the new promotion:")
    add_name = st.text_input("Promotion Name*", max_chars=150)
    add_desc = st.text_area("Description")
    add_type = st.selectbox("Discount Type*", options=["PERCENT", "FIXED"])
    add_value = st.number_input("Discount Value*", min_value=0.0, step=0.01, format="%.2f", help="Amount for FIXED, percentage for PERCENT (e.g., 10 for 10%)")
    add_start_date = st.date_input("Start Date (Optional)", value=None)
    add_end_date = st.date_input("End Date (Optional)", value=None)
    add_points = st.number_input("Required Points (Optional, for Loyalty)", min_value=0, step=10, value=None, placeholder="Leave blank if not point-based")

    submitted_add = st.form_submit_button("Add Promotion")
    if submitted_add:
        # Basic validation
        if not add_name:
            st.warning("Promotion Name is required.")
        elif add_value <= 0:
             st.warning("Discount Value must be positive.")
        elif add_end_date and add_start_date and add_end_date < add_start_date:
             st.warning("End Date cannot be before Start Date.")
        else:
            # Handle optional fields potentially being None for DB
            start_date_db = add_start_date if add_start_date else None
            end_date_db = add_end_date if add_end_date else None
            req_points_db = int(add_points) if add_points is not None and add_points > 0 else None

            sql = """
            INSERT INTO Promotions
            (PromotionName, Description, DiscountType, DiscountValue, StartDate, EndDate, RequiredPoints)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            params = (add_name, add_desc, add_type, add_value, start_date_db, end_date_db, req_points_db)
            success, _ = run_command(sql, params)
            if success:
                st.success(f"Promotion '{add_name}' added successfully!")

st.divider()

# --- Edit Existing Promotion ---
st.subheader("Edit Existing Promotion")
promo_list = run_query("SELECT PromotionID, PromotionName FROM Promotions ORDER BY PromotionName;")
if not promo_list.empty:
    promo_options = {f"{row['PromotionName']} (ID: {row['PromotionID']})": row['PromotionID'] for index, row in promo_list.iterrows()}
    selected_promo_display = st.selectbox("Select Promotion to Edit", options=promo_options.keys())

    if selected_promo_display:
        selected_promo_id = promo_options[selected_promo_display]
        current_promo_data = run_query("SELECT * FROM Promotions WHERE PromotionID = %s;", params=(selected_promo_id,))

        if not current_promo_data.empty:
            promo = current_promo_data.iloc[0]
            discount_type_index = ["PERCENT", "FIXED"].index(promo['DiscountType']) if promo['DiscountType'] in ["PERCENT", "FIXED"] else 0

            with st.form(f"edit_promo_{selected_promo_id}"):
                st.write(f"Editing: {promo['PromotionName']}")
                edit_name = st.text_input("Promotion Name*", value=promo['PromotionName'], max_chars=150)
                edit_desc = st.text_area("Description", value=promo['Description'] or "")
                edit_type = st.selectbox("Discount Type*", options=["PERCENT", "FIXED"], index=discount_type_index)
                edit_value = st.number_input("Discount Value*", value=float(promo['DiscountValue']), min_value=0.0, step=0.01, format="%.2f")
                edit_start_date = st.date_input("Start Date (Optional)", value=promo['StartDate']) # handles None okay
                edit_end_date = st.date_input("End Date (Optional)", value=promo['EndDate'])
                edit_points = st.number_input("Required Points (Optional)", value=promo['RequiredPoints'], min_value=0, step=10, placeholder="Leave blank if not point-based")

                submitted_edit = st.form_submit_button("Update Promotion")
                if submitted_edit:
                    if not edit_name: st.warning("Promotion Name required.")
                    elif edit_value <= 0: st.warning("Discount Value must be positive.")
                    elif edit_end_date and edit_start_date and edit_end_date < edit_start_date: st.warning("End Date cannot be before Start Date.")
                    else:
                        start_date_db = edit_start_date if edit_start_date else None
                        end_date_db = edit_end_date if edit_end_date else None
                        req_points_db = int(edit_points) if edit_points is not None and edit_points > 0 else None

                        sql_update = """
                            UPDATE Promotions SET
                            PromotionName=%s, Description=%s, DiscountType=%s, DiscountValue=%s,
                            StartDate=%s, EndDate=%s, RequiredPoints=%s
                            WHERE PromotionID=%s;
                        """
                        params_update = (edit_name, edit_desc, edit_type, edit_value, start_date_db, end_date_db, req_points_db, selected_promo_id)
                        success, _ = run_command(sql_update, params_update)
                        if success:
                            st.success(f"Promotion '{edit_name}' updated successfully!")
                            st.rerun()
else:
    st.info("No promotions available to edit.")

st.divider()

# --- Delete Existing Promotion ---
st.subheader("Delete Existing Promotion")
if not promo_list.empty:
    promo_options_del = {f"{row['PromotionName']} (ID: {row['PromotionID']})": row['PromotionID'] for index, row in promo_list.iterrows()}
    selected_promo_display_del = st.selectbox("Select Promotion to Delete", options=promo_options_del.keys(), key="delete_promo_select")

    if selected_promo_display_del:
        selected_promo_id_del = promo_options_del[selected_promo_display_del]
        promo_name_del = selected_promo_display_del.split(" (ID:")[0]

        if st.button(f"Confirm Delete Promotion: {promo_name_del}"):
            # Check AppliedPromotions (FK is RESTRICT)
            applied_exist = run_query("SELECT COUNT(*) as count FROM AppliedPromotions WHERE PromotionID = %s;", params=(selected_promo_id_del,))
            if applied_exist.iloc[0]['count'] > 0:
                st.error(f"Cannot delete promotion. It has been applied to {applied_exist.iloc[0]['count']} order(s). (Deletion restricted by database constraint).")
            else:
                sql_delete = "DELETE FROM Promotions WHERE PromotionID = %s;"
                params_delete = (selected_promo_id_del,)
                success, _ = run_command(sql_delete, params_delete)
                if success:
                    st.success(f"Promotion '{promo_name_del}' deleted successfully!")
                    st.rerun()
else:
    st.info("No promotions available to delete.")