-- Temporarily change the delimiter
DELIMITER $$

-- Procedure 1: Add New Customer 
CREATE PROCEDURE sp_AddCustomer (
    IN p_FirstName VARCHAR(100),
    IN p_LastName VARCHAR(100),
    IN p_Email VARCHAR(255),
    IN p_PhoneNumber VARCHAR(50),
    OUT p_NewCustomerID INT
)
BEGIN
    -- Basic Input Validation
    IF p_FirstName IS NULL OR p_FirstName = '' OR p_LastName IS NULL OR p_LastName = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'First name and last name cannot be empty.';
    END IF;

    IF p_Email IS NULL OR p_Email = '' OR p_Email NOT LIKE '_%@_%._%' THEN
         SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A valid email address is required.';
    END IF;

    -- Check if email already exists
    IF EXISTS (SELECT 1 FROM Customers WHERE Email = p_Email) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email address already exists.';
    END IF;

    -- Insert the new customer
    INSERT INTO Customers (FirstName, LastName, Email, PhoneNumber, JoinDate, LoyaltyPoints)
    VALUES (p_FirstName, p_LastName, p_Email, p_PhoneNumber, CURDATE(), 0);

    -- Get the automatically generated CustomerID for the new customer
    SET p_NewCustomerID = LAST_INSERT_ID();

END$$


-- Procedure 2: Process Order
CREATE PROCEDURE sp_ProcessOrder (
    IN p_CustomerID INT,
    IN p_EmployeeID INT,
    IN p_StoreID INT,
    IN p_ProductIDsAndQuantities TEXT,
    IN p_PointsToRedeem INT,
    OUT p_NewOrderID INT
)
BEGIN
    -- 1. Declare ALL variables first
    DECLARE v_OrderID INT;
    DECLARE v_SubTotal DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_FinalTotal DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_RedeemedValue DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_PointsEarned INT DEFAULT 0;
    DECLARE v_CustomerPointsAvailable INT DEFAULT 0;
    DECLARE v_ItemString TEXT DEFAULT p_ProductIDsAndQuantities;
    DECLARE v_Delimiter CHAR(1) DEFAULT ',';
    DECLARE v_ItemPair VARCHAR(50);
    DECLARE v_ProductID INT;
    DECLARE v_Quantity INT;
    DECLARE v_ProductPrice DECIMAL(10, 2);
    DECLARE v_Stock INT;
    DECLARE v_Pos INT;
    DECLARE v_ErrorMessage VARCHAR(255); -- <<<< Added variable for error message

    -- 2. Declare Handlers AFTER variables but BEFORE other logic
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END; -- Added semicolon is correct

    -- Now proceed with the rest of the logic...
    -- Basic validation for required IDs
    IF p_EmployeeID IS NULL OR NOT EXISTS (SELECT 1 FROM Employees WHERE EmployeeID = p_EmployeeID) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid or missing EmployeeID.';
    END IF;
    IF p_StoreID IS NULL OR NOT EXISTS (SELECT 1 FROM Stores WHERE StoreID = p_StoreID) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid or missing StoreID.';
    END IF;
    IF p_CustomerID IS NOT NULL AND NOT EXISTS (SELECT 1 FROM Customers WHERE CustomerID = p_CustomerID) THEN
         SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid CustomerID provided.';
    END IF;
     IF p_ProductIDsAndQuantities IS NULL OR p_ProductIDsAndQuantities = '' THEN
         SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order must contain at least one item.';
    END IF;

    -- Start Transaction
    START TRANSACTION;

    -- Handle Point Redemption
    SET p_PointsToRedeem = COALESCE(p_PointsToRedeem, 0);
    IF p_CustomerID IS NOT NULL AND p_PointsToRedeem > 0 THEN
        SET v_CustomerPointsAvailable = fn_GetCustomerLoyaltyPoints(p_CustomerID);
        IF v_CustomerPointsAvailable < p_PointsToRedeem THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient loyalty points.';
        END IF;
        SET v_RedeemedValue = p_PointsToRedeem / 100.0;
    END IF;

    -- Create Initial Order record
    INSERT INTO Orders (CustomerID, EmployeeID, StoreID, OrderTimestamp, TotalAmount, PointsEarned, PointsRedeemed)
    VALUES (p_CustomerID, p_EmployeeID, p_StoreID, NOW(), 0.00, 0, p_PointsToRedeem);
    SET v_OrderID = LAST_INSERT_ID();

    -- Process Order Items Loop
    SET v_ItemString = CONCAT(v_ItemString, v_Delimiter);
    WHILE LOCATE(v_Delimiter, v_ItemString) > 0 DO
        SET v_Pos = LOCATE(v_Delimiter, v_ItemString);
        SET v_ItemPair = TRIM(SUBSTRING(v_ItemString, 1, v_Pos - 1));
        SET v_ItemString = SUBSTRING(v_ItemString, v_Pos + 1);
        SET v_ProductID = CONVERT(SUBSTRING_INDEX(v_ItemPair, ':', 1), UNSIGNED INTEGER);
        SET v_Quantity = CONVERT(SUBSTRING_INDEX(v_ItemPair, ':', -1), UNSIGNED INTEGER);

        IF v_ProductID <= 0 OR v_Quantity <= 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid ProductID or Quantity format in item list.';
        END IF;

        SELECT Price, StockQuantity INTO v_ProductPrice, v_Stock FROM Products WHERE ProductID = v_ProductID;

        IF v_ProductPrice IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid ProductID found in order items.';
        END IF;

        -- ****** REFACTORED STOCK CHECK ******
        IF v_Stock < v_Quantity THEN
             -- 1. Set the error message variable
             SET v_ErrorMessage = CONCAT('Insufficient stock for ProductID: ', v_ProductID);
             -- 2. Use the variable in the SIGNAL statement
             SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_ErrorMessage;
        END IF;
        -- ****** END OF REFACTOR ******

        INSERT INTO OrderItems (OrderID, ProductID, Quantity, PriceAtTimeOfOrder)
        VALUES (v_OrderID, v_ProductID, v_Quantity, v_ProductPrice);
        SET v_SubTotal = v_SubTotal + (v_Quantity * v_ProductPrice);
    END WHILE;

    -- Calculate Final Total
    SET v_FinalTotal = v_SubTotal - v_RedeemedValue;
    IF v_FinalTotal < 0 THEN SET v_FinalTotal = 0.00; END IF;

    -- Calculate Points Earned
    IF p_CustomerID IS NOT NULL THEN SET v_PointsEarned = fn_CalculatePointsEarned(v_FinalTotal);
    ELSE SET v_PointsEarned = 0; END IF;

    -- Update Order with totals
    UPDATE Orders SET TotalAmount = v_FinalTotal, PointsEarned = v_PointsEarned WHERE OrderID = v_OrderID;

    -- Update Customer Loyalty Points
    IF p_CustomerID IS NOT NULL THEN
        UPDATE Customers SET LoyaltyPoints = LoyaltyPoints + v_PointsEarned - p_PointsToRedeem WHERE CustomerID = p_CustomerID;
    END IF;

    -- Commit
    COMMIT;

    -- Set output parameter
    SET p_NewOrderID = v_OrderID;

END$$

-- Change the delimiter back to the standard semicolon
DELIMITER ;