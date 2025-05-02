# pages/07_Reports.py
"""
Streamlit page for displaying various aggregated reports.
"""

import streamlit as st
import pandas as pd
from database import run_query

st.set_page_config(page_title="Reports", layout="wide")
st.title("📊 Reports Dashboard") # Added emoji
st.write("View aggregated data and performance metrics.")

st.divider()

# --- Report 1: Top Selling Products ---
st.subheader("Top Selling Products (by Revenue)")
try:
    # Query already sorts by revenue descending
    query_top_prod = """
    SELECT ProductName, Category, TotalQuantitySold, TotalRevenue
    FROM vw_ProductSalesPerformance
    ORDER BY TotalRevenue DESC
    LIMIT 10;
    """
    df_top_products = run_query(query_top_prod)
    if not df_top_products.empty:
        st.dataframe(df_top_products, hide_index=True, use_container_width=True, column_config={
            "TotalRevenue": st.column_config.NumberColumn(format="$%.2f")
        })
        # Bar chart - data is passed sorted by revenue DESC
        st.bar_chart(df_top_products.set_index('ProductName')['TotalRevenue'])
    else:
        st.info("No product performance data found.")
except Exception as e:
    st.error(f"Error loading top products report: {e}")


st.divider()

# --- Report 2: Monthly Sales Summary ---
st.subheader("Monthly Sales Summary")
try:
    query_monthly = """
    SELECT
        DATE_FORMAT(OrderTimestamp, '%Y-%m') AS SaleMonth,
        COUNT(OrderID) AS NumberOfOrders,
        SUM(TotalAmount) AS MonthlyRevenue
    FROM Orders
    GROUP BY SaleMonth
    ORDER BY SaleMonth DESC;
    """
    df_monthly = run_query(query_monthly)
    if not df_monthly.empty:
         st.dataframe(df_monthly, hide_index=True, use_container_width=True, column_config={
             "MonthlyRevenue": st.column_config.NumberColumn(format="$%.2f")
         })
         # Prepare data for chart: Set index and sort chronologically ASC
         df_monthly_chart = df_monthly.set_index('SaleMonth')
         df_monthly_chart = df_monthly_chart.sort_index(ascending=True) # Sort index for chart
         st.bar_chart(df_monthly_chart['MonthlyRevenue'])
    else:
         st.info("No monthly sales data found.")
except Exception as e:
    st.error(f"Error loading monthly sales report: {e}")

st.divider()

# --- Report 3: Top Customers ---
st.subheader("Top Customers (by Total Spent)")
try:
    # Query already sorts by TotalSpent DESC
    query_top_cust = """
    SELECT FirstName, LastName, Email, TotalOrders, TotalSpent
    FROM vw_CustomerOrderSummary
    ORDER BY TotalSpent DESC
    LIMIT 10;
    """
    df_top_cust = run_query(query_top_cust)
    if not df_top_cust.empty:
        st.dataframe(df_top_cust, hide_index=True, use_container_width=True, column_config={
             "TotalSpent": st.column_config.NumberColumn(format="$%.2f")
         })
        # Optional: Chart top customers spent
        st.bar_chart(df_top_cust.set_index('Email')['TotalSpent']) # Using Email as unique index
    else:
        st.info("No top customer data found.")
except Exception as e:
    st.error(f"Error loading top customers report: {e}")


st.divider()

# --- Report 4: Low Stock Items ---
st.subheader("Low Stock Alert (Items <= 10)")
try:
    low_stock_threshold = 10
    query_low_stock = "SELECT ProductID, ProductName, Category, StockQuantity FROM Products WHERE StockQuantity <= %s ORDER BY StockQuantity ASC;"
    df_low_stock = run_query(query_low_stock, params=(low_stock_threshold,))
    if not df_low_stock.empty:
        st.dataframe(df_low_stock, hide_index=True, use_container_width=True)
    else:
        st.info(f"No products found with stock at or below {low_stock_threshold}.")
except Exception as e:
    st.error(f"Error loading low stock report: {e}")