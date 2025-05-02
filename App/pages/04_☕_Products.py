# pages/04_Products.py
"""
Streamlit page for managing Product information (CRUD operations).
"""

import streamlit as st
import pandas as pd
from database import run_query, run_command

st.set_page_config(page_title="Product Management", layout="wide")
st.title("☕ Product Management")
st.write("View, Add, Edit, or Delete Products in the catalog.")

# --- Display Existing Products ---
st.subheader("Product Catalog")
df_products = run_query("SELECT * FROM Products ORDER BY Category, ProductName;")
if not df_products.empty:
    st.dataframe(df_products, use_container_width=True, hide_index=True, column_config={
        "Price": st.column_config.NumberColumn(format="$%.2f"),
        "StockQuantity": st.column_config.NumberColumn(label="Stock Qty")
    })
else:
    st.info("No products found.")

st.divider()

# --- Add New Product Form ---
st.subheader("Add New Product")
with st.form("add_product_form", clear_on_submit=True):
    st.write("Enter details for the new product:")
    add_name = st.text_input("Product Name*", max_chars=150)
    add_category = st.text_input("Category", max_chars=100, placeholder="e.g., Beverage, Food, Merchandise")
    add_price = st.number_input("Price*", min_value=0.00, step=0.01, format="%.2f")
    add_stock = st.number_input("Initial Stock Quantity*", min_value=0, step=1)

    submitted_add = st.form_submit_button("Add Product")
    if submitted_add:
        # Basic validation
        if not add_name:
            st.warning("Product Name is required.")
        elif add_price < 0:
             st.warning("Price cannot be negative.")
        elif add_stock < 0:
             st.warning("Stock Quantity cannot be negative.")
        else:
            sql = """
            INSERT INTO Products (ProductName, Category, Price, StockQuantity)
            VALUES (%s, %s, %s, %s);
            """
            params = (add_name, add_category, add_price, add_stock)
            success, _ = run_command(sql, params)
            if success:
                st.success(f"Product '{add_name}' added successfully!")

st.divider()

# --- Edit Existing Product ---
st.subheader("Edit Existing Product")
product_list = run_query("SELECT ProductID, ProductName, Category FROM Products ORDER BY Category, ProductName;")
if not product_list.empty:
    prod_options = {f"{row['ProductName']} ({row['Category'] or 'N/A'}) - ID: {row['ProductID']}": row['ProductID'] for index, row in product_list.iterrows()}
    selected_prod_display = st.selectbox("Select Product to Edit", options=prod_options.keys())

    if selected_prod_display:
        selected_prod_id = prod_options[selected_prod_display]
        current_prod_data = run_query("SELECT * FROM Products WHERE ProductID = %s;", params=(selected_prod_id,))

        if not current_prod_data.empty:
            prod = current_prod_data.iloc[0]

            with st.form(f"edit_product_{selected_prod_id}"):
                st.write(f"Editing: {prod['ProductName']}")
                edit_name = st.text_input("Product Name*", value=prod['ProductName'], max_chars=150)
                edit_category = st.text_input("Category", value=prod['Category'], max_chars=100)
                edit_price = st.number_input("Price*", value=float(prod['Price']), min_value=0.00, step=0.01, format="%.2f")
                edit_stock = st.number_input("Stock Quantity*", value=int(prod['StockQuantity']), min_value=0, step=1)

                submitted_edit = st.form_submit_button("Update Product")
                if submitted_edit:
                    if not edit_name:
                         st.warning("Product Name is required.")
                    elif edit_price < 0:
                         st.warning("Price cannot be negative.")
                    elif edit_stock < 0:
                         st.warning("Stock Quantity cannot be negative.")
                    else:
                        sql_update = """
                            UPDATE Products
                            SET ProductName=%s, Category=%s, Price=%s, StockQuantity=%s
                            WHERE ProductID=%s;
                        """
                        params_update = (edit_name, edit_category, edit_price, edit_stock, selected_prod_id)
                        success, _ = run_command(sql_update, params_update)
                        if success:
                            st.success(f"Product '{edit_name}' updated successfully!")
                            st.rerun()
else:
    st.info("No products available to edit.")

st.divider()

# --- Delete Existing Product ---
st.subheader("Delete Existing Product")
if not product_list.empty:
    prod_options_del = {f"{row['ProductName']} ({row['Category'] or 'N/A'}) - ID: {row['ProductID']}": row['ProductID'] for index, row in product_list.iterrows()}
    selected_prod_display_del = st.selectbox("Select Product to Delete", options=prod_options_del.keys(), key="delete_prod_select")

    if selected_prod_display_del:
        selected_prod_id_del = prod_options_del[selected_prod_display_del]
        prod_name_del = selected_prod_display_del.split(" (")[0]

        if st.button(f"Confirm Delete Product: {prod_name_del}"):
            # Check OrderItems (FK is RESTRICT)
            items_exist = run_query("SELECT COUNT(*) as count FROM OrderItems WHERE ProductID = %s;", params=(selected_prod_id_del,))
            if items_exist.iloc[0]['count'] > 0:
                st.error(f"Cannot delete product. It exists in {items_exist.iloc[0]['count']} past order item(s). (Deletion restricted by database constraint).")
            else:
                sql_delete = "DELETE FROM Products WHERE ProductID = %s;"
                params_delete = (selected_prod_id_del,)
                success, _ = run_command(sql_delete, params_delete)
                if success:
                    st.success(f"Product '{prod_name_del}' deleted successfully!")
                    st.rerun()
else:
    st.info("No products available to delete.")