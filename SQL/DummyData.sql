-- 1. Stores
INSERT INTO Stores (StoreName, Address, City, State, ZipCode) VALUES
('Downtown Brew', '123 Main St', 'Anytown', 'NY', '10001'),
('Uptown Cafe', '456 Oak Ave', 'Anytown', 'NY', '10025');

-- 2. Employees (Requires StoreIDs 1, 2 to exist)
INSERT INTO Employees (FirstName, LastName, Position, HireDate, HourlyRate, StoreID) VALUES
('Alice', 'Smith', 'Manager', '2023-05-15', 25.50, 1),
('Bob', 'Johnson', 'Barista', '2024-01-10', 18.00, 1),
('Charlie', 'Davis', 'Barista', '2024-03-01', 18.50, 2);

-- 3. Customers
INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber, JoinDate, LoyaltyPoints) VALUES
('Eva', 'Martinez', 'eva.m@email.com', '555-1111', '2024-08-20', 50),
('Frank', 'Garcia', 'frank.g@email.com', NULL, '2025-01-05', 120),
('Grace', 'Lee', 'grace.l@email.com', '555-3333', CURDATE(), 0),
('Henry', 'Wilson', 'henry.w@email.com', '555-4444', '2024-11-11', 25);

-- 4. Products
INSERT INTO Products (ProductName, Category, Price, StockQuantity) VALUES
('Espresso', 'Beverage', 3.50, 100),
('Latte', 'Beverage', 4.50, 80),
('Cappuccino', 'Beverage', 4.25, 75),
('Iced Coffee', 'Beverage', 4.00, 90),
('Croissant', 'Food', 2.75, 50),
('Muffin', 'Food', 3.00, 60),
('Coffee Beans (1lb)', 'Merchandise', 15.00, 30),
('Shop Mug', 'Merchandise', 12.00, 40);

-- 5. Promotions
INSERT INTO Promotions (PromotionName, Description, DiscountType, DiscountValue, StartDate, EndDate, RequiredPoints) VALUES
('Spring Discount', '10% off entire order in Spring', 'PERCENT', 10.00, '2025-03-01', '2025-05-31', NULL),
('Loyal Sip Reward', '$2 off when redeeming 200 points', 'FIXED', 2.00, NULL, NULL, 200),
('Muffin Madness', '$0.50 off any Muffin', 'FIXED', 0.50, '2025-05-01', '2025-05-15', NULL);

-- 6. Manually Inserted Past Orders & Items (for testing views)
-- Assumes first Customer is ID 1, second is ID 2, etc.
-- Assumes first Employee is ID 1, second is ID 2, etc.
-- Assumes first Product is ID 1, second is ID 2, etc.

-- Order 1 (Eva - CustID 1, Bob - EmpID 2, Store 1)
INSERT INTO Orders (CustomerID, EmployeeID, StoreID, OrderTimestamp, TotalAmount, PointsEarned, PointsRedeemed) VALUES
(1, 2, 1, '2025-04-28 09:15:00', 7.25, 7, 0);
SET @Order1ID = LAST_INSERT_ID();
INSERT INTO OrderItems (OrderID, ProductID, Quantity, PriceAtTimeOfOrder) VALUES
(@Order1ID, 2, 1, 4.50), -- Latte
(@Order1ID, 5, 1, 2.75); -- Croissant

-- Order 2 (Frank - CustID 2, Charlie - EmpID 3, Store 2)
INSERT INTO Orders (CustomerID, EmployeeID, StoreID, OrderTimestamp, TotalAmount, PointsEarned, PointsRedeemed) VALUES
(2, 3, 2, '2025-04-30 14:30:00', 11.00, 11, 0);
SET @Order2ID = LAST_INSERT_ID();
INSERT INTO OrderItems (OrderID, ProductID, Quantity, PriceAtTimeOfOrder) VALUES
(@Order2ID, 4, 2, 4.00), -- Iced Coffee
(@Order2ID, 6, 1, 3.00); -- Muffin

-- Order 3 (Guest, Alice - EmpID 1, Store 1)
INSERT INTO Orders (CustomerID, EmployeeID, StoreID, OrderTimestamp, TotalAmount, PointsEarned, PointsRedeemed) VALUES
(NULL, 1, 1, '2025-05-01 11:05:00', 3.50, 0, 0);
SET @Order3ID = LAST_INSERT_ID();
INSERT INTO OrderItems (OrderID, ProductID, Quantity, PriceAtTimeOfOrder) VALUES
(@Order3ID, 1, 1, 3.50); -- Espresso