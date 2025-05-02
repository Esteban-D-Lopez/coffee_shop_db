# pages/06_Orders.py
"""
Streamlit page for viewing past Orders and creating new ones
using the sp_ProcessOrder stored procedure.
"""

import streamlit as st
import pandas as pd
from database import run_query, run_command, call_sp_process_order # Import database functions
import datetime
from decimal import Decimal # Use Decimal for currency precision

st.set_page_config(page_title="Order Management", layout="wide")
st.title("🛒 Order Management") 

tab1, tab2 = st.tabs(["View Past Orders", "Create New Order"])

# --- Tab 1: View Past Orders  ---
with tab1:
    st.header("View Past Orders")
    st.write("Displaying recent orders.")
    # (Keep the existing code for Tab 1 as it was)
    query_orders = """
        SELECT
            o.OrderID, o.OrderTimestamp,
            CONCAT(c.FirstName, ' ', c.LastName) AS CustomerName, c.CustomerID,
            CONCAT(e.FirstName, ' ', e.LastName) AS EmployeeName,
            s.StoreName,
            o.TotalAmount, o.PointsEarned, o.PointsRedeemed
        FROM Orders o
        LEFT JOIN Customers c ON o.CustomerID = c.CustomerID
        JOIN Employees e ON o.EmployeeID = e.EmployeeID
        JOIN Stores s ON o.StoreID = s.StoreID
        ORDER BY o.OrderTimestamp DESC
        LIMIT 50;
    """
    df_orders = run_query(query_orders)
    if not df_orders.empty:
        st.dataframe(df_orders, hide_index=True, use_container_width=True, column_config={
             "TotalAmount": st.column_config.NumberColumn(format="$%.2f"),
             "OrderTimestamp": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm:ss")
        })
        st.divider()
        st.subheader("View Order Details")
        order_ids = df_orders['OrderID'].tolist()
        selected_order_id = st.selectbox("Select OrderID to view items", options=order_ids, index=None, placeholder="Choose an Order ID...", key="view_order_items_select")
        if selected_order_id:
             query_items = """
                SELECT oi.OrderItemID, p.ProductName, oi.Quantity, oi.PriceAtTimeOfOrder
                FROM OrderItems oi
                JOIN Products p ON oi.ProductID = p.ProductID
                WHERE oi.OrderID = %s;
             """
             df_items = run_query(query_items, params=(selected_order_id,))
             if not df_items.empty:
                  st.write(f"Items for Order ID: {selected_order_id}")
                  st.dataframe(df_items, hide_index=True, use_container_width=True, column_config={
                       "PriceAtTimeOfOrder": st.column_config.NumberColumn(format="$%.2f")
                  })
             else:
                  st.info("No items found for this order.")
    else:
        st.info("No past orders found.")


# --- Tab 2: Create New Order ---
with tab2:
    st.header("Create New Order")

    # --- Fetch data for dropdowns (Run once at the start) ---
    employees = run_query("SELECT EmployeeID, FirstName, LastName FROM Employees ORDER BY LastName, FirstName;")
    stores = run_query("SELECT StoreID, StoreName FROM Stores ORDER BY StoreName;")
    customers = run_query("SELECT CustomerID, FirstName, LastName, Email FROM Customers ORDER BY LastName, FirstName;")
    products = run_query("SELECT ProductID, ProductName, Price, StockQuantity FROM Products ORDER BY ProductName;")

    # --- Fetch Active Promotions ---
    active_promos_query = "SELECT PromotionID, PromotionName, Description, DiscountType, DiscountValue FROM Promotions WHERE (StartDate IS NULL OR StartDate <= CURDATE()) AND (EndDate IS NULL OR EndDate >= CURDATE()) AND RequiredPoints IS NULL;"
    df_active_promos = run_query(active_promos_query)
    active_promo_options = {row['PromotionName']: row['PromotionID'] for index, row in df_active_promos.iterrows()} if not df_active_promos.empty else {}
    active_promo_details = {row['PromotionID']: row for index, row in df_active_promos.iterrows()} if not df_active_promos.empty else {}

    # --- Create dictionaries for dropdowns ---
    employee_options = {f"{row['LastName']}, {row['FirstName']} (ID: {row['EmployeeID']})": row['EmployeeID'] for index, row in employees.iterrows()} if not employees.empty else {}
    store_options = {f"{row['StoreName']} (ID: {row['StoreID']})": row['StoreID'] for index, row in stores.iterrows()} if not stores.empty else {}
    customer_options = {"Guest Order (No Customer)": None}
    if not customers.empty:
        customer_options.update({f"{row['LastName']}, {row['FirstName']} ({row['Email']})": row['CustomerID'] for index, row in customers.iterrows()})
    product_options = {f"{row['ProductName']} (ID: {row['ProductID']}) - ${row['Price']:.2f}": row['ProductID'] for index, row in products.iterrows()} if not products.empty else {}

    # --- Initialize session state ---
    if 'order_items' not in st.session_state: st.session_state.order_items = {}
    if 'points_redeem_input' not in st.session_state: st.session_state.points_redeem_input = 0 # Initialize points input state

    # --- Manage Order Items ---
    st.subheader("Build Order Items")
    st.markdown("Add products to the order:")
    col_item, col_qty, col_add_btn = st.columns([3, 1, 1])
    with col_item: selected_product_display = st.selectbox("Select Product", options=product_options.keys(), index=None, placeholder="Choose a product...", key="add_product_select")
    with col_qty: add_qty = st.number_input("Quantity", min_value=1, step=1, value=1, key="add_qty_input")
    with col_add_btn:
        st.markdown("<br/>", unsafe_allow_html=True)
        add_button_clicked = st.button("Add Item", key="add_item_button")
    if add_button_clicked:
        if selected_product_display:
            prod_id_to_add = product_options[selected_product_display]
            prod_info_rows = products[products['ProductID'] == prod_id_to_add]
            if not prod_info_rows.empty:
                 prod_info = prod_info_rows.iloc[0]
                 current_stock = prod_info['StockQuantity']
                 current_qty_in_cart = st.session_state.order_items.get(prod_id_to_add, 0)
                 if (current_qty_in_cart + add_qty) <= current_stock:
                      st.session_state.order_items[prod_id_to_add] = current_qty_in_cart + add_qty
                      st.success(f"Added {add_qty} x {prod_info['ProductName']}.")
                 else: st.warning(f"Cannot add {add_qty}. Only {current_stock} in stock (and {current_qty_in_cart} already in cart). Max add: {current_stock - current_qty_in_cart}")
            else: st.error("Product data not found (should not happen).") # Added error check
        else: st.warning("Please select a product to add.")
    st.markdown("---")

    # Display Current Items and Remove Item Section 
    if st.session_state.order_items:
        st.write("**Current Items in Order:**")
        items_list = []; total_sub = Decimal("0.00")
        for prod_id, qty in st.session_state.order_items.items():
             prod_info_rows = products[products['ProductID'] == prod_id]
             if not prod_info_rows.empty:
                 prod_info = prod_info_rows.iloc[0]
                 price = Decimal(str(prod_info['Price'])); subtotal = qty * price
                 items_list.append({"Product": prod_info['ProductName'], "ID": prod_id, "Qty": qty, "Price": price, "Subtotal": subtotal})
                 total_sub += subtotal
             else: items_list.append({"Product": f"Unknown (ID:{prod_id})", "ID": prod_id, "Qty": qty, "Price": Decimal("0.00"), "Subtotal": Decimal("0.00")})
        st.dataframe(pd.DataFrame(items_list), hide_index=True, column_config={"Price": st.column_config.NumberColumn(format="$%.2f"),"Subtotal": st.column_config.NumberColumn(format="$%.2f")})
        st.write(f"**Subtotal: ${total_sub:.2f}**")
        st.markdown("Remove items from the order:")
        remove_options = {f"{item['Product']} (Qty: {item['Qty']})": item['ID'] for item in items_list}
        selected_item_to_remove_display = st.selectbox("Select Item to Remove", options=remove_options.keys(), index=None, placeholder="Choose an item...", key="remove_item_select")
        remove_button_clicked = st.button("Remove Selected Item", key="remove_item_button")
        if remove_button_clicked:
            if selected_item_to_remove_display:
                item_id_to_remove = remove_options[selected_item_to_remove_display]
                if item_id_to_remove in st.session_state.order_items:
                    del st.session_state.order_items[item_id_to_remove]
                    st.success("Item removed."); st.rerun()
            else: st.warning("Please select an item to remove.")
    else: st.info("No items added yet.")

    st.divider()

    # --- Order Header Inputs  ---
    st.subheader("Order Details")
    col1, col2 = st.columns(2)
    with col1:
        selected_employee_display = st.selectbox("Employee Processing Order*", options=employee_options.keys(), index=None, key="order_emp_select")
        selected_store_display = st.selectbox("Store Location*", options=store_options.keys(), index=None, key="order_store_select")
    with col2:
        selected_customer_display = st.selectbox("Customer*", options=customer_options.keys(), index=0, key="order_cust_select")
        customer_id = customer_options.get(selected_customer_display) # Get current customer ID

        # --- Points Input ---
        # Tied to session state, enabled/disabled based on customer_id
        st.number_input(
            "Points to Redeem",
            min_value=0, step=10,
            key="points_redeem_input", # Use session state key
            disabled=(customer_id is None), # Enable only if a customer is selected
        )

    # --- Promotion Selection  ---
    # --- Final Submit Form ---
    with st.form("finalize_order_form"):
        st.markdown("**Apply General Promotions (Optional)**")
        selected_promo_names = st.multiselect(
            "Select active promotions:",
            options=active_promo_options.keys(),
            key="promo_multiselect"
        )

        st.divider()
        # The SUBMIT button for the form
        submitted_order = st.form_submit_button("Process Order")

        if submitted_order:
            # Retrieve values needed for the procedure call
            # Employee/Store/Customer are selected outside the form, get current value
            employee_id = employee_options.get(selected_employee_display)
            store_id = store_options.get(selected_store_display)
            # customer_id already retrieved above
            # Retrieve points from SESSION STATE as it's outside the form
            points_to_redeem = int(st.session_state.points_redeem_input) if customer_id is not None else 0

            # Validation
            if not employee_id or not store_id:
                st.warning("Employee and Store must be selected.")
            elif not st.session_state.order_items:
                st.warning("Order must contain at least one item.")
            # Optional: Add validation for points redemption vs customer's actual points here if desired
            else:
                items_string = ",".join([f"{pid}:{qty}" for pid, qty in st.session_state.order_items.items()])

                # 1. Call SP
                st.info("Processing base order and loyalty points...")
                success_sp, new_order_id = call_sp_process_order(
                    customer_id, employee_id, store_id, items_string, points_to_redeem
                )

                if success_sp and new_order_id:
                    st.success(f"Base order created (ID: {new_order_id}). Applying promotions...")
                    total_promo_discount = Decimal("0.00")
                    applied_promo_details_msg = []

                    # 2. Apply selected general promotions (get promo details selected IN the form)
                    selected_promo_ids = [active_promo_options[name] for name in selected_promo_names if name in active_promo_options]

                    if selected_promo_ids:
                        df_order_total = run_query("SELECT TotalAmount FROM Orders WHERE OrderID = %s", params=(new_order_id,))
                        if not df_order_total.empty:
                            order_total_before_promos = Decimal(str(df_order_total.iloc[0]['TotalAmount']))

                            for promo_id in selected_promo_ids:
                                if promo_id in active_promo_details:
                                    promo_detail = active_promo_details[promo_id]
                                    discount_this_promo = Decimal("0.00")
                                    promo_type = promo_detail['DiscountType']
                                    promo_value = Decimal(str(promo_detail['DiscountValue']))

                                    if promo_type == 'PERCENT':
                                        discount_this_promo = (order_total_before_promos * promo_value / Decimal("100.0")).quantize(Decimal("0.01"))
                                    elif promo_type == 'FIXED':
                                        discount_this_promo = promo_value

                                    remaining_total = order_total_before_promos - total_promo_discount
                                    discount_this_promo = min(discount_this_promo, remaining_total)

                                    if discount_this_promo > 0:
                                        applied_sql = "INSERT INTO AppliedPromotions (OrderID, PromotionID, DiscountAmountApplied) VALUES (%s, %s, %s);"
                                        applied_params = (new_order_id, promo_id, float(discount_this_promo))
                                        success_applied, _ = run_command(applied_sql, applied_params)
                                        if success_applied:
                                            total_promo_discount += discount_this_promo
                                            applied_promo_details_msg.append(f"{promo_detail['PromotionName']}: -${discount_this_promo:.2f}")
                                        else: st.error(f"Failed to apply promotion '{promo_detail['PromotionName']}'.")
                                else: st.warning(f"Details not found for promo ID {promo_id}. Skipping.")

                            if total_promo_discount > 0:
                                st.info(f"Updating final total with promotion discount: ${total_promo_discount:.2f}")
                                update_total_sql = "UPDATE Orders SET TotalAmount = TotalAmount - %s WHERE OrderID = %s;"
                                update_params = (float(total_promo_discount), new_order_id)
                                success_update, _ = run_command(update_total_sql, update_params)
                                if not success_update: st.error("Failed to update final order total.")

                    # Final success message
                    final_message = f"Order Processed Successfully! New Order ID: {new_order_id}."
                    if applied_promo_details_msg: final_message += " Promotions applied: " + ", ".join(applied_promo_details_msg)
                    st.success(final_message)

                    # Clear items and points input from state
                    st.session_state.order_items = {}
                    st.rerun()

                else:
                    st.error("Failed to process base order. See error message above if available.")