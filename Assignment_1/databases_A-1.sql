show databases;
DROP DATABASE mess_management;
CREATE DATABASE mess_management;


USE mess_management;
-- 1. Member Table (Mandatory)
CREATE TABLE Member (
    MemberID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Age INT NOT NULL CHECK (Age >= 16), 
    Email VARCHAR(100) UNIQUE NOT NULL,
    ContactNumber VARCHAR(15) NOT NULL,
    Role VARCHAR(20) NOT NULL CHECK (Role IN ('Student', 'Admin', 'Staff'))
);
-- 1.1 Students
CREATE TABLE Student (
    StudentID INT PRIMARY KEY,
    MemberID INT UNIQUE NOT NULL,
    HostelBlock VARCHAR(50) NOT NULL,
    RoomNo VARCHAR(20) NOT NULL,
    Program VARCHAR(20) NOT NULL
        CHECK (Program IN ('BTech', 'MTech', 'MSc', 'PhD', 'MBA')),
    FOREIGN KEY (MemberID)
        REFERENCES Member(MemberID)
        ON DELETE CASCADE
);
-- 1.2 Staff
CREATE TABLE Staff (
    StaffID INT PRIMARY KEY,
    MemberID INT UNIQUE NOT NULL,
    JobRole VARCHAR(50) NOT NULL,   -- Cook, Cleaner, Manager
    Salary DECIMAL(10,2) CHECK (Salary >= 0),
    HireDate DATE NOT NULL,
    FOREIGN KEY (MemberID)
        REFERENCES Member(MemberID)
        ON DELETE CASCADE
);

-- 2. MenuItem Table
CREATE TABLE MenuItem (
    ItemID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Category VARCHAR(50) NOT NULL
);

-- 3. DailySchedule Table
CREATE TABLE DailySchedule (
    ScheduleID INT PRIMARY KEY,
    MealDate DATE NOT NULL,
    MealType VARCHAR(20) NOT NULL CHECK (MealType IN ('Breakfast', 'Lunch', 'Snacks', 'Dinner')),
    IsActive BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. Schedule_Items Table (Resolves the M:M relationship from UML)
CREATE TABLE Schedule_Items (
    ScheduleID INT NOT NULL,
    ItemID INT NOT NULL,
    QuantityPrepared INT NOT NULL CHECK (QuantityPrepared >= 0),
    Unit varchar(10) NOT NULL,
    PRIMARY KEY (ScheduleID, ItemID),
    FOREIGN KEY (ScheduleID) REFERENCES DailySchedule(ScheduleID) ON DELETE CASCADE,
    FOREIGN KEY (ItemID) REFERENCES MenuItem(ItemID) ON DELETE CASCADE
);

-- 5. Inventory Table
CREATE TABLE Inventory (
    IngredientID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    StockQty DECIMAL(10,2) NOT NULL
        CHECK (StockQty >= 0),
    Unit VARCHAR(20) NOT NULL,
    MinStockLevel DECIMAL(10,2) NOT NULL
        CHECK (MinStockLevel >= 0),
    ReorderLevel DECIMAL(10,2)
        CHECK (ReorderLevel >= 0),
    LastUpdated DATE
);


-- 6. Recipe Table (Resolves the M:M between MenuItem and Inventory)
CREATE TABLE Recipe (
    RecipeID INT PRIMARY KEY,
    ItemID INT NOT NULL,
    IngredientID INT NOT NULL,
    QtyRequired DECIMAL(10, 2) NOT NULL CHECK (QtyRequired > 0),
    FOREIGN KEY (ItemID) REFERENCES MenuItem(ItemID) ON DELETE CASCADE,
    FOREIGN KEY (IngredientID) REFERENCES Inventory(IngredientID) ON DELETE CASCADE
);

-- 7. MealLog Table
CREATE TABLE MealLog (
    LogID INT PRIMARY KEY,
    MemberID INT NOT NULL,
    ScheduleID INT NOT NULL,
    Status VARCHAR(20) NOT NULL CHECK (Status IN ('Consumed', 'Missed', 'Opted-Out')),
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE,
    FOREIGN KEY (ScheduleID) REFERENCES DailySchedule(ScheduleID) ON DELETE CASCADE
);

-- 8. Bill Table
CREATE TABLE MonthlyMessPayment (
    MonthlyPaymentID INT PRIMARY KEY,
    MemberID INT NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    Amount DECIMAL(10,2) NOT NULL
        CHECK (Amount >= 0),
    Status VARCHAR(20) NOT NULL
        CHECK (Status IN ('Paid', 'Pending')),
    FOREIGN KEY (MemberID)
        REFERENCES Member(MemberID)
        ON DELETE CASCADE,
    CHECK (EndDate > StartDate)
);
CREATE TABLE MealPayment (
    MealPaymentID INT PRIMARY KEY,
    MemberID INT NOT NULL,
    ScheduleID INT NOT NULL,
    Amount DECIMAL(10,2) NOT NULL
        CHECK (Amount >= 0),
    PaymentDate DATE NOT NULL,
    FOREIGN KEY (MemberID)
        REFERENCES Member(MemberID)
        ON DELETE CASCADE,
    FOREIGN KEY (ScheduleID)
        REFERENCES DailySchedule(ScheduleID)
        ON DELETE CASCADE
);


-- 9. Supplier Table
CREATE TABLE Supplier (
    SupplierID INT PRIMARY KEY,
    CompanyName VARCHAR(100) NOT NULL,
    ContactName VARCHAR(100) NOT NULL,
    Phone VARCHAR(15) NOT NULL,
    Address VARCHAR(100) NOT NULL,
    SupplierType VARCHAR(100) NOT NULL
);
CREATE TABLE Purchase (
    PurchaseID INT PRIMARY KEY,
    SupplierID INT NOT NULL,
    IngredientID INT NOT NULL,
    Quantity DECIMAL(10,2) NOT NULL
        CHECK (Quantity > 0),
    UnitPrice DECIMAL(10,2) NOT NULL
        CHECK (UnitPrice >= 0),
    TotalCost DECIMAL(12,2) NOT NULL
        CHECK (TotalCost >= 0),
    PurchaseDate DATE NOT NULL,
    FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
        ON DELETE CASCADE,
    FOREIGN KEY (IngredientID) REFERENCES Inventory(IngredientID)
        ON DELETE CASCADE
);

-- 10. WasteLog Table
CREATE TABLE WasteLog (
    WasteID INT PRIMARY KEY,
    ScheduleID INT NOT NULL,
    WasteQty_Kg DECIMAL(10, 2) NOT NULL CHECK (WasteQty_Kg >= 0),
    Waste_category varchar(15) NOT NULL,
    RecordedDate DATE NOT NULL,
    FOREIGN KEY (ScheduleID) REFERENCES DailySchedule(ScheduleID) ON DELETE CASCADE
);
-- 11. Rating Table
CREATE TABLE MessRating (
    RatingID INT PRIMARY KEY,
    ScheduleID INT NOT NULL,
    Rating INT NOT NULL CHECK (Rating BETWEEN 1 AND 5),
    RatedOn DATE NOT NULL,
    FOREIGN KEY (ScheduleID) REFERENCES DailySchedule(ScheduleID)
        ON DELETE CASCADE
);
-- 12. Staff Shif Table
CREATE TABLE StaffShiftLog (
    ShiftLogID INT PRIMARY KEY,
    StaffID INT NOT NULL,
    ShiftDate DATE NOT NULL,
    ShiftType VARCHAR(20) NOT NULL
        CHECK (ShiftType IN ('Morning', 'Evening', 'Night')),
    CheckInTime TIME NOT NULL,
    CheckOutTime TIME,
    TotalHours DECIMAL(5,2)
        CHECK (TotalHours >= 0),
    FOREIGN KEY (StaffID) REFERENCES Staff(StaffID)
        ON DELETE CASCADE,
    -- Logical constraint: checkout must be after checkin
    CHECK (
        CheckOutTime IS NULL 
        OR CheckOutTime > CheckInTime
    )
);
SHOW TABLES;


INSERT INTO Member VALUES
(1,'Amit Shah',20,'amit@uni.edu','9876543210','Student'),
(2,'Riya Patel',21,'riya@uni.edu','9876543211','Student'),
(3,'Karan Mehta',22,'karan@uni.edu','9876543212','Student'),
(4,'Neha Jain',23,'neha@uni.edu','9876543213','Student'),
(5,'Rahul Verma',19,'rahul@uni.edu','9876543214','Student'),
(6,'Sneha Iyer',24,'sneha@uni.edu','9876543215','Student'),
(7,'Mr. Verma',40,'verma@mess.com','9876543216','Staff'),
(8,'Suresh Cook',35,'suresh@mess.com','9876543217','Staff'),
(9,'Ramesh Helper',32,'ramesh@mess.com','9876543218','Staff'),
(10,'Admin Rao',45,'rao@mess.com','9876543219','Admin');

INSERT INTO Student VALUES
(23110366,1,'A','101','BTech'),
(23110367,2,'A','102','BTech'),
(23110368,3,'B','201','MTech'),
(23110369,4,'B','202','MBA'),
(23110370,5,'C','301','MSc'),
(23110371,6,'C','302','PhD');


INSERT INTO Staff VALUES
(201,7,'Manager',30000,'2022-06-01'),
(202,8,'Cook',18000,'2023-01-15'),
(203,9,'Helper',12000,'2023-03-10');

INSERT INTO MenuItem VALUES
(1,'Poha','Breakfast'),
(2,'Idli','Breakfast'),
(3,'Upma','Breakfast'),
(4,'Rice','Lunch'),
(5,'Dal','Lunch'),
(6,'Paneer Curry','Dinner'),
(7,'Chapati','Dinner'),
(8,'Veg Biryani','Dinner'),
(9,'Samosa','Snacks'),
(10,'Tea','Snacks');

INSERT INTO DailySchedule VALUES
(1,'2026-02-10','Breakfast',TRUE),
(2,'2026-02-10','Lunch',TRUE),
(3,'2026-02-10','Dinner',TRUE),
(4,'2026-02-11','Breakfast',TRUE),
(5,'2026-02-11','Lunch',TRUE),
(6,'2026-02-11','Dinner',TRUE),
(7,'2026-02-12','Breakfast',TRUE),
(8,'2026-02-12','Lunch',TRUE),
(9,'2026-02-12','Dinner',TRUE),
(10,'2026-02-13','Breakfast',TRUE);

INSERT INTO Inventory VALUES
(1,'Rice',120,'Kg',50,70,'2026-02-01'),
(2,'Wheat Flour',100,'Kg',40,60,'2026-02-01'),
(3,'Milk',60,'Liters',20,30,'2026-02-01'),
(4,'Potato',90,'Kg',30,50,'2026-02-01'),
(5,'Onion',70,'Kg',25,40,'2026-02-01'),
(6,'Tomato',65,'Kg',25,40,'2026-02-01'),
(7,'Paneer',30,'Kg',10,20,'2026-02-01'),
(8,'Oil',40,'Liters',15,25,'2026-02-01'),
(9,'Tea Leaves',20,'Kg',8,12,'2026-02-01'),
(10,'Spices Mix',15,'Kg',5,8,'2026-02-01');

INSERT INTO Recipe VALUES
(1,4,1,0.20),
(2,5,4,0.10),
(3,6,7,0.15),
(4,7,2,0.12),
(5,1,4,0.08),
(6,2,3,0.05),
(7,8,1,0.25),
(8,9,4,0.06),
(9,10,9,0.02),
(10,6,8,0.03);

INSERT INTO Schedule_Items VALUES
(1,1,120,'Plates'),
(1,2,100,'Plates'),
(2,4,150,'Plates'),
(2,5,140,'Plates'),
(3,6,130,'Plates'),
(3,7,200,'Pieces'),
(4,3,110,'Plates'),
(5,4,160,'Plates'),
(6,8,125,'Plates'),
(7,1,115,'Plates');

INSERT INTO Supplier VALUES
(1,'FreshFarm Foods','Ramesh Patel','9876500001','Ahmedabad','Vegetables'),
(2,'Amul Dairy','Suresh Shah','9876500002','Anand','Dairy'),
(3,'GrainHub Traders','Mahesh Jain','9876500003','Surat','Grains'),
(4,'Oil Depot','Nitin Shah','9876500004','Vadodara','Oil'),
(5,'Spice World','Amit Gupta','9876500005','Rajkot','Spices'),
(6,'Veggie Supply','Ravi Kumar','9876500006','Delhi','Vegetables'),
(7,'Farm Fresh','Kishore','9876500007','Pune','Vegetables'),
(8,'Dairy Best','Imran','9876500008','Mumbai','Dairy'),
(9,'Golden Grains','Harsh','9876500009','Jaipur','Grains'),
(10,'Kitchen Needs','Manoj','9876500010','Indore','Mixed');

INSERT INTO Purchase VALUES
(1,3,1,200,45,9000,'2026-02-01'),
(2,3,2,150,35,5250,'2026-02-02'),
(3,2,3,100,52,5200,'2026-02-03'),
(4,1,4,120,20,2400,'2026-02-03'),
(5,2,7,50,280,14000,'2026-02-04'),
(6,4,8,60,120,7200,'2026-02-05'),
(7,5,10,30,200,6000,'2026-02-06'),
(8,6,5,90,18,1620,'2026-02-06'),
(9,7,6,80,22,1760,'2026-02-07'),
(10,9,1,150,44,6600,'2026-02-08');

INSERT INTO MealLog VALUES
(1,1,1,'Consumed'),
(2,2,1,'Consumed'),
(3,3,1,'Missed'),
(4,4,2,'Consumed'),
(5,5,2,'Consumed'),
(6,6,3,'Opted-Out'),
(7,1,3,'Consumed'),
(8,2,2,'Consumed'),
(9,3,3,'Consumed'),
(10,4,1,'Missed');

INSERT INTO MonthlyMessPayment VALUES
(1,1,'2026-02-01','2026-02-28',3000,'Paid'),
(2,2,'2026-02-01','2026-02-28',3000,'Pending'),
(3,3,'2026-02-01','2026-02-28',3000,'Paid'),
(4,4,'2026-02-01','2026-02-28',3000,'Paid'),
(5,5,'2026-02-01','2026-02-28',3000,'Pending'),
(6,6,'2026-02-01','2026-02-28',3000,'Paid'),
(7,1,'2026-01-01','2026-01-31',3000,'Paid'),
(8,2,'2026-01-01','2026-01-31',3000,'Paid'),
(9,3,'2026-01-01','2026-01-31',3000,'Paid'),
(10,4,'2026-01-01','2026-01-31',3000,'Paid');

INSERT INTO MealPayment VALUES
(1,1,1,50,'2026-02-10'),
(2,2,1,50,'2026-02-10'),
(3,3,2,80,'2026-02-10'),
(4,4,2,80,'2026-02-10'),
(5,5,3,100,'2026-02-10'),
(6,6,3,100,'2026-02-10'),
(7,1,4,50,'2026-02-11'),
(8,2,4,50,'2026-02-11'),
(9,3,5,80,'2026-02-11'),
(10,4,6,100,'2026-02-11');

INSERT INTO WasteLog VALUES
(1,1,5,'Solid','2026-02-10'),
(2,2,8,'Solid','2026-02-10'),
(3,3,6,'Liquid','2026-02-10'),
(4,4,4,'Solid','2026-02-11'),
(5,5,7,'Solid','2026-02-11'),
(6,6,5,'Liquid','2026-02-11'),
(7,7,3,'Solid','2026-02-12'),
(8,8,6,'Solid','2026-02-12'),
(9,9,4,'Liquid','2026-02-12'),
(10,10,2,'Solid','2026-02-13');

INSERT INTO MessRating VALUES
(1,1,4,'2026-02-10'),
(2,2,5,'2026-02-10'),
(3,3,3,'2026-02-10'),
(4,4,4,'2026-02-11'),
(5,5,2,'2026-02-11'),
(6,6,5,'2026-02-11'),
(7,7,4,'2026-02-12'),
(8,8,3,'2026-02-12'),
(9,9,5,'2026-02-12'),
(10,10,4,'2026-02-13');

INSERT INTO StaffShiftLog VALUES
(1,201,'2026-02-10','Morning','06:00','14:00',8),
(2,202,'2026-02-10','Evening','14:00','22:00',8),
(3,203,'2026-02-10','Night','22:00','23:59',2),
(4,201,'2026-02-11','Morning','06:00','14:00',8),
(5,202,'2026-02-11','Evening','14:00','22:00',8),
(6,203,'2026-02-11','Night','22:00','23:59',2),
(7,201,'2026-02-12','Morning','06:00','14:00',8),
(8,202,'2026-02-12','Evening','14:00','22:00',8),
(9,203,'2026-02-12','Night','22:00','23:59',2),
(10,202,'2026-02-13','Morning','06:00','14:00',8);




-- Functionality 1: Student Meal Attendance & Consumption Tracking
-- Solves: Tracking which students consumed, missed, or opted out of meals

SELECT ds.MealDate,ds.MealType,ml.Status,
       COUNT(*) AS TotalStudents
FROM MealLog ml
JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
GROUP BY ds.MealDate, ds.MealType, ml.Status
ORDER BY ds.MealDate;

-- Functionality 2: Menu Planning & Daily Menu Management
-- Solves: Students viewing daily menu & admins managing dishes
SELECT ds.MealDate, ds.MealType, mi.Name AS DishName,mi.Category,
       si.QuantityPrepared, si.Unit
FROM DailySchedule ds
JOIN Schedule_Items si
     ON ds.ScheduleID = si.ScheduleID
JOIN MenuItem mi
     ON si.ItemID = mi.ItemID
WHERE ds.MealDate = '2026-02-10';

-- Functionality 3: Automated Monthly Billing System
-- Solves: Tracking paid and pending mess fees
SELECT m.Name AS StudentName, mp.Amount,mp.StartDate, mp.EndDate, mp.Status
FROM MonthlyMessPayment mp
JOIN Member m
     ON mp.MemberID = m.MemberID
ORDER BY mp.Status;

-- Functionality 4: Inventory & Grocery Stock Management
-- Solves: Detecting low stock & reorder requirements
SELECT Name AS IngredientName, StockQty, Unit, ReorderLevel
FROM Inventory
WHERE StockQty <= ReorderLevel;

-- Functionality 5: Supplier & Expense Management
-- Solves: Monitoring total spending per supplier
SELECT s.CompanyName, SUM(p.TotalCost) AS TotalExpense
FROM Purchase p
JOIN Supplier s
     ON p.SupplierID = s.SupplierID
GROUP BY s.CompanyName
ORDER BY TotalExpense DESC;

-- Functionality 6: Food Waste Tracking & Analysis
-- Solves: Measuring food waste per meal
SELECT ds.MealDate, ds.MealType, w.WasteQty_Kg
FROM WasteLog w
JOIN DailySchedule ds
     ON w.ScheduleID = ds.ScheduleID
ORDER BY ds.MealDate;

-- Functionality 7: Meal Rating
-- Solves: Evaluating food quality & student satisfaction
SELECT ds.MealDate, ds.MealType, AVG(mr.Rating) AS AverageRating
FROM MessRating mr
JOIN DailySchedule ds
     ON mr.ScheduleID = ds.ScheduleID
GROUP BY ds.MealDate, ds.MealType
ORDER BY AverageRating DESC;
