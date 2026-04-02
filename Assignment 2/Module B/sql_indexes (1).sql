-- ============================================================
--  Module B – SubTask 4: SQL Indexing Strategy
--  CS 432 Databases | Mess Management System
-- ============================================================
--  Run this file AFTER databases_A-1.sql
--  Each index is justified by the exact API query it optimises.
-- ============================================================

USE mess_management;

-- ──────────────────────────────────────────────────────────
--  INDEX 1: DailySchedule(MealDate)
--  Fixes: Full table scan on /menu route
--  Query: WHERE ds.MealDate = '2026-02-10'
--  Before: type=ALL, rows=10
--  After:  type=ref,  rows=3 (only matching dates scanned)
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_meal_date
    ON DailySchedule(MealDate);

-- ──────────────────────────────────────────────────────────
--  INDEX 2: MonthlyMessPayment(Status, StartDate)
--  Fixes: filesort on /billing admin view
--  Query: ORDER BY mp.Status DESC, mp.StartDate DESC
--  Composite index covers both ORDER BY columns, eliminating
--  the need for MySQL to sort the result set in memory.
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_payment_status_date
    ON MonthlyMessPayment(Status, StartDate);

-- ──────────────────────────────────────────────────────────
--  INDEX 3: MealLog(MemberID)
--  Fixes: Full scan on /meal_attendance (student view)
--  Query: WHERE ml.MemberID = %s  (also used in /dashboard)
--  Every student login triggers this query — high frequency.
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_meallog_member
    ON MealLog(MemberID);

-- ──────────────────────────────────────────────────────────
--  INDEX 4: MealLog(ScheduleID)
--  Fixes: JOIN lookup on MealLog for admin attendance view
--  Query: JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
--  Without this, MySQL scans all MealLog rows for every
--  ScheduleID value from DailySchedule.
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_meallog_schedule
    ON MealLog(ScheduleID);

-- ──────────────────────────────────────────────────────────
--  INDEX 5: MonthlyMessPayment(MemberID)
--  Fixes: WHERE MemberID = %s on student billing view
--  Query: WHERE MemberID = %s ORDER BY StartDate DESC
--  Every student visiting /billing triggers a lookup by
--  MemberID — critical for per-user performance.
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_payment_member
    ON MonthlyMessPayment(MemberID);

-- ──────────────────────────────────────────────────────────
--  INDEX 6: StaffShiftLog(StaffID)
--  Fixes: WHERE StaffID = (...) in staff /dashboard
--  Query: WHERE StaffID = (SELECT StaffID FROM Staff
--                          WHERE MemberID = %s)
--  The subquery result is used as a lookup key; without the
--  index MySQL scans all shift rows.
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_shift_staff
    ON StaffShiftLog(StaffID);

-- ──────────────────────────────────────────────────────────
--  INDEX 7: Purchase(SupplierID)
--  Fixes: LEFT JOIN in /suppliers aggregate query
--  Query: LEFT JOIN Purchase p ON s.SupplierID = p.SupplierID
--         GROUP BY s.SupplierID ORDER BY TotalSpent DESC
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_purchase_supplier
    ON Purchase(SupplierID);

-- ──────────────────────────────────────────────────────────
--  INDEX 8: MessRating(ScheduleID)
--  Fixes: JOIN lookup in /ratings aggregation query
--  Query: JOIN DailySchedule ds ON mr.ScheduleID = ds.ScheduleID
--         GROUP BY ds.MealDate, ds.MealType
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_rating_schedule
    ON MessRating(ScheduleID);

-- ──────────────────────────────────────────────────────────
--  INDEX 9: WasteLog(ScheduleID)
--  Fixes: JOIN lookup in /waste query
--  Query: JOIN DailySchedule ds ON w.ScheduleID = ds.ScheduleID
--         ORDER BY w.RecordedDate DESC
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_waste_schedule
    ON WasteLog(ScheduleID);

-- ──────────────────────────────────────────────────────────
--  Verify all indexes were created
-- ──────────────────────────────────────────────────────────
SELECT
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE,
    INDEX_TYPE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'mess_management'
  AND INDEX_NAME   != 'PRIMARY'
ORDER BY TABLE_NAME, INDEX_NAME;
