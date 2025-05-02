-- View 1: Customer Order Summary
-- Shows basic customer info, total number of orders, and total amount spent.
CREATE VIEW vw_CustomerOrderSummary AS
SELECT
    c.CustomerID,
    c.FirstName,
    c.LastName,
    c.Email,
    COUNT(o.OrderID) AS TotalOrders,
    -- Use COALESCE to show 0 if a customer has no orders, instead of NULL
    COALESCE(SUM(o.TotalAmount), 0) AS TotalSpent
FROM
    Customers c
    -- LEFT JOIN includes all customers, even those without orders
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
GROUP BY
    c.CustomerID, c.FirstName, c.LastName, c.Email;


-- View 2: Product Sales Performance
-- Shows product details, total quantity sold, total revenue, and average selling price.
CREATE VIEW vw_ProductSalesPerformance AS
SELECT
    p.ProductID,
    p.ProductName,
    p.Category,
    -- Use COALESCE to show 0 for products never sold
    COALESCE(SUM(oi.Quantity), 0) AS TotalQuantitySold,
    COALESCE(SUM(oi.Quantity * oi.PriceAtTimeOfOrder), 0) AS TotalRevenue,
    -- AVG will be NULL if the product was never sold, which is acceptable here
    AVG(oi.PriceAtTimeOfOrder) AS AverageSellingPrice
FROM
    Products p
    -- LEFT JOIN includes all products, even those never sold
    LEFT JOIN OrderItems oi ON p.ProductID = oi.ProductID
GROUP BY
    p.ProductID, p.ProductName, p.Category;