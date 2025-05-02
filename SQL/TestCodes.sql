SELECT * FROM Stores;
SELECT * FROM Employees;
SELECT * FROM Customers;
SELECT * FROM Products;
SELECT * FROM Promotions;
SELECT * FROM Orders;
SELECT * FROM OrderItems;

-- Check stock quantities after orders (should be reduced)
SELECT ProductID, ProductName, StockQuantity FROM Products WHERE ProductID IN (1, 2, 4, 5, 6);

-- Check views
SELECT * FROM vw_CustomerOrderSummary;
SELECT * FROM vw_ProductSalesPerformance;

-- -- Check Stored Procedures
-- Test sp_AddCustomer
-- Provide sample data and declare variable for OUT parameter
CALL sp_AddCustomer('Sarah', 'Chen', 'sarah.c@email.com', '555-9876', @new_cust_id);

-- Check the CustomerID returned by the procedure
SELECT @new_cust_id AS NewCustomerID_From_Procedure;

-- Verify the customer was actually inserted into the table
SELECT * FROM Customers WHERE CustomerID = @new_cust_id;


-- Test sp_ProcessOrder - Scenario 1: New Order, No Points Redeemed
-- Customer 1 (Eva), Employee 2 (Bob), Store 1 (Downtown Brew)
-- Items: 1 Latte (ID 2), 1 Croissant (ID 5) -> '2:1,5:1'
-- Points Redeemed: 0
CALL sp_ProcessOrder(1, 2, 1, '2:1,5:1', 0, @new_ord_id1);

-- Check the OrderID returned
SELECT @new_ord_id1 AS NewOrderID_Scenario1;

-- Verify the Order details (TotalAmount = 4.50 + 2.75 = 7.25, PointsEarned = 7)
SELECT * FROM Orders WHERE OrderID = @new_ord_id1;

-- Verify the OrderItems were inserted
SELECT * FROM OrderItems WHERE OrderID = @new_ord_id1;

-- Verify stock was reduced (Check initial stock - quantity ordered)
-- Initial: Latte=80, Croissant=50. After manual inserts: Latte=79, Croissant=49
-- Should be: Latte=78, Croissant=48
SELECT ProductID, ProductName, StockQuantity FROM Products WHERE ProductID IN (2, 5);

-- Verify Customer 1's points (Initial 50 + 7 manual + 7 from this order = 64)
SELECT CustomerID, FirstName, LoyaltyPoints FROM Customers WHERE CustomerID = 1;



-- Test sp_ProcessOrder - Scenario 2: Order with Points Redeemed
-- Customer 2 (Frank), Employee 3 (Charlie), Store 2 (Uptown Cafe)
-- Items: 1 Coffee Beans (ID 7) -> '7:1'
-- Points Redeemed: 100 (Value = $1.00)
CALL sp_ProcessOrder(2, 3, 2, '7:1', 100, @new_ord_id2);

-- Check the OrderID returned
SELECT @new_ord_id2 AS NewOrderID_Scenario2;

-- Verify the Order details
-- TotalAmount = 15.00 (subtotal) - 1.00 (redeemed) = 14.00
-- PointsEarned = FLOOR(14.00) = 14
-- PointsRedeemed = 100
SELECT * FROM Orders WHERE OrderID = @new_ord_id2;

-- Verify the OrderItems were inserted
SELECT * FROM OrderItems WHERE OrderID = @new_ord_id2;

-- Verify stock was reduced (Coffee Beans: Initial 30 -> Should be 29)
SELECT ProductID, ProductName, StockQuantity FROM Products WHERE ProductID = 7;

-- Verify Customer 2's points
-- Initial: 120 points. Manual Order: +11 points. This Order: +14 points earned, -100 points redeemed.
-- Total = 120 + 11 + 14 - 100 = 45 points
SELECT CustomerID, FirstName, LoyaltyPoints FROM Customers WHERE CustomerID = 2;