-- Temporarily change the delimiter
DELIMITER $$

-- Trigger 1: Update Stock Quantity After Order Item Insert
-- Fires automatically AFTER a row is inserted into the OrderItems table.
CREATE TRIGGER trg_UpdateStockAfterOrder
AFTER INSERT ON OrderItems -- Specifies the event and table
FOR EACH ROW -- Executes the trigger body for each row inserted
BEGIN
    -- Decrease the StockQuantity in the Products table
    -- NEW refers to the row that was just inserted into OrderItems
    UPDATE Products
    SET StockQuantity = StockQuantity - NEW.Quantity -- Subtract the quantity ordered
    WHERE ProductID = NEW.ProductID; -- For the specific product that was ordered
END$$

-- Change the delimiter back to the standard semicolon
DELIMITER ;