-- Temporarily change the delimiter so I can use ; inside the function bodies
DELIMITER $$

-- Function 1: Get Customer Loyalty Points
-- Takes a CustomerID and returns their current points balance.
CREATE FUNCTION fn_GetCustomerLoyaltyPoints (p_CustomerID INT)
RETURNS INT
DETERMINISTIC -- Indicates the function gives the same result for the same input
READS SQL DATA -- Indicates the function only reads data, doesn't modify it
BEGIN
    DECLARE points INT;

    -- Select the points for the given customer.
    -- Use COALESCE to return 0 if the customer is not found or points are NULL.
    SELECT COALESCE(LoyaltyPoints, 0) INTO points
    FROM Customers
    WHERE CustomerID = p_CustomerID;

    -- Return 0 if the customer wasn't found (points will be NULL from the SELECT)
    RETURN COALESCE(points, 0);
END$$


-- Function 2: Calculate Points Earned
-- Takes an order total and calculates points based on shop rules.
CREATE FUNCTION fn_CalculatePointsEarned (p_OrderTotal DECIMAL(10,2))
RETURNS INT
DETERMINISTIC -- This calculation logic is deterministic
NO SQL -- Indicates the function doesn't need to access database tables
BEGIN
    -- Business Rule Example: 1 point for every whole dollar spent.
    -- Ensure total is not negative before calculating.
    IF p_OrderTotal < 0 THEN
        RETURN 0;
    END IF;
    -- FLOOR rounds the result down to the nearest whole number.
    RETURN FLOOR(p_OrderTotal);
END$$

-- Change the delimiter back to the standard semicolon
DELIMITER ;