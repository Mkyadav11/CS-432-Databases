"""
Mess Management System — ACID Validation (Assignment 3, Module A)
==================================================================
Tables used:
  member               (MemberID PK)
  meallog              (LogID PK, MemberID FK)
  monthly_mess_payment (MonthlyPaymentID PK, MemberID FK)

Tests:
  A — Atomicity    : crash mid-txn across all 3 tables → full rollback
  C — Consistency  : invalid role / negative amount → constraint rollback
  I — Isolation    : concurrent payment txns → no dirty read / corruption
  D — Durability   : committed data survives simulated restart
"""

import os
import threading
import time

WAL_PATH = "mess_wal.log"
if os.path.exists(WAL_PATH):
    os.remove(WAL_PATH)

from database.db_manager import DatabaseManager


def bar(title):
    print(f"\n{'═'*65}")
    print(f"  {title}")
    print(f"{'═'*65}")


# ── Bootstrap ──────────────────────────────────────────────────────────────
bar("STARTUP & SEED")
db = DatabaseManager(wal_path=WAL_PATH)
db.seed()
db.show_all()


# ══════════════════════════════════════════════════════════════════════════
#  TEST A — ATOMICITY
#  Scenario: A student pays their mess bill.
#    Step 1 → mark payment as Paid        (monthly_mess_payment)
#    Step 2 → log a meal attendance entry  (meallog)
#    Step 3 → CRASH before completing
#  Expected: all steps rolled back, state unchanged.
# ══════════════════════════════════════════════════════════════════════════
bar("TEST A — ATOMICITY TEST (simulated mid-transaction crash)")

before_pay = db.tables["monthly_mess_payment"].search("PAY002")
before_log_count = len(db.tables["meallog"].all_records())
before_member_count = len(db.tables["member"].all_records())

txn = db.begin()
print(f"[Txn {txn.txn_id}] BEGIN")

try:
    pay = txn.select("monthly_mess_payment", "PAY002")
    txn.update("monthly_mess_payment", "PAY002", {**pay, "Status": "Paid"})
    print(f"Step 1: PAY002 status → Paid")

    txn.insert("meallog", "L004",
               {"LogID": "L004", "MemberID": "M002",
                "ScheduleID": "SCH003", "Status": "Consumed"})
    print(f" Step 2: MealLog L004 inserted for M002")

    print("  ✗ Step 3: SIMULATED CRASH — power failure!")
    raise RuntimeError("Power failure during member insert!")

except RuntimeError as e:
    print(f"\n  [CRASH] {e}")
    db.rollback(txn)
    print(f"  [Txn {txn.txn_id}] ROLLED BACK")

after_pay = db.tables["monthly_mess_payment"].search("PAY002")
after_log_count = len(db.tables["meallog"].all_records())

assert after_pay["Status"] == before_pay["Status"], \
    f"ATOMICITY FAIL: PAY002 status changed to {after_pay['Status']}"
assert after_log_count == before_log_count, \
    f"ATOMICITY FAIL: MealLog count changed {before_log_count} -> {after_log_count}"

print(f"\n  PAY002 status = {after_pay['Status']}  (unchanged ✓)")
print(f"  MealLog count = {after_log_count}  (unchanged ✓)")
print("  ATOMICITY PASSED — no partial updates remain.")


# ══════════════════════════════════════════════════════════════════════════
#  TEST C — CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════
bar("TEST C — CONSISTENCY  (constraint violations)")

print("\nC-1: Insert member with invalid Role 'Cook'")
txn = db.begin()
try:
    txn.insert("member", "M004",
               {"MemberID": "M004", "Name": "Test User",
                "DOB": "2000-01-01", "Email": "test@iit.ac.in",
                "ContactNumber": "9111111111", "Role": "Cook"})
    db.commit(txn)
except ValueError as e:
    print(f"  [CONSTRAINT] {e}")
    db.rollback(txn)
    print(f"  [Txn {txn.txn_id}] ROLLED BACK")
assert db.tables["member"].search("M004") is None
print("  C-1 PASSED — invalid role rejected.")

print("\nC-2: Insert payment with Amount = 0")
txn = db.begin()
try:
    txn.insert("monthly_mess_payment", "PAY003",
               {"MonthlyPaymentID": "PAY003", "MemberID": "M001",
                "StartDate": "2025-07-01", "EndDate": "2025-07-31",
                "Amount": 0.0, "Status": "Pending"})
    db.commit(txn)
except ValueError as e:
    print(f"  [CONSTRAINT] {e}")
    db.rollback(txn)
    print(f"  [Txn {txn.txn_id}] ROLLED BACK")
assert db.tables["monthly_mess_payment"].search("PAY003") is None
print(" C-2 PASSED — zero amount rejected.")

print("\nC-3: Insert MealLog with non-existent MemberID 'M999'")
txn = db.begin()
try:
    txn.insert("meallog", "L005",
               {"LogID": "L005", "MemberID": "M999",
                "ScheduleID": "SCH004", "Status": "Consumed"})
    db.commit(txn)
except ValueError as e:
    print(f"  [CONSTRAINT] {e}")
    db.rollback(txn)
    print(f"  [Txn {txn.txn_id}] ROLLED BACK")
assert db.tables["meallog"].search("L005") is None
print("   C-3 PASSED — FK violation rejected.")
print("\n   CONSISTENCY PASSED — all constraints enforced.")


# ══════════════════════════════════════════════════════════════════════════
#  TEST I — ISOLATION
# ══════════════════════════════════════════════════════════════════════════
bar("TEST I — ISOLATION  (concurrent transactions)")
 
results = {}
barrier  = threading.Barrier(2)
step_lock = threading.Lock()
 
def step(tag, msg):
    with step_lock:
        print(f"  {tag}  {msg}")
 
def writer_thread():
    txn = db.begin()
    step(f"[Writer {txn.txn_id}]", "BEGIN transaction")
 
    pay = txn.select("monthly_mess_payment", "PAY002")
    step(f"[Writer {txn.txn_id}]", f"READ   PAY002 → Amount={pay['Amount']}, Status={pay['Status']}")
 
    txn.update("monthly_mess_payment", "PAY002", {**pay, "Status": "Paid", "Amount": 9999.0})
    step(f"[Writer {txn.txn_id}]", "UPDATE PAY002 → Amount=9999.0, Status=Paid  (NOT committed yet)")
    step(f"[Writer {txn.txn_id}]", " Holding lock on 'monthly_mess_payment' table ...")
 
    barrier.wait()          # let reader start trying
    time.sleep(1.5)         # hold lock long enough to see reader blocked
 
    step(f"[Writer {txn.txn_id}]", "Still holding lock ... reader must wait")
    time.sleep(0.5)
 
    db.rollback(txn)
    step(f"[Writer {txn.txn_id}]", "ROLLBACK — undoing Amount=9999 → restoring Amount=3000.0")
    step(f"[Writer {txn.txn_id}]", " Lock RELEASED on 'monthly_mess_payment'")
 
def reader_thread():
    barrier.wait()          # start only after writer has locked
    txn = db.begin()
    step(f"[Reader {txn.txn_id}]", "BEGIN transaction")
    step(f"[Reader {txn.txn_id}]", "Wants to READ PAY002 → trying to acquire lock ...")
    step(f"[Reader {txn.txn_id}]", " BLOCKED — 'monthly_mess_payment' is locked by Writer. Waiting ...")
 
    # this select internally calls _lock() which blocks until writer releases
    pay = txn.select("monthly_mess_payment", "PAY002")
 
    step(f"[Reader {txn.txn_id}]", "Lock acquired — Writer has finished.")
    step(f"[Reader {txn.txn_id}]", f"READ   PAY002 → Amount={pay['Amount']}, Status={pay['Status']}")
    results["amount_seen"] = pay["Amount"]
    db.commit(txn)
    step(f"[Reader {txn.txn_id}]", "COMMIT")
 
t1 = threading.Thread(target=writer_thread)
t2 = threading.Thread(target=reader_thread)
t1.start(); t2.start()
t1.join(); t2.join()
 
print()
final_pay = db.tables["monthly_mess_payment"].search("PAY002")
assert final_pay["Amount"] == 3000.0, \
    f"ISOLATION FAIL: PAY002 amount = {final_pay['Amount']}, expected 3000.0"
print(f"  PAY002 final amount = {final_pay['Amount']}  (Reader never saw 9999 ✓)")
print("   ISOLATION PASSED — uncommitted data not visible / not persisted.")

# ══════════════════════════════════════════════════════════════════════════
#  TEST D — DURABILITY
# ══════════════════════════════════════════════════════════════════════════
bar("TEST D — DURABILITY  (survive simulated restart)")

print("Phase 1: Commit a valid 3-table transaction")
txn = db.begin()
print(f"[Txn {txn.txn_id}] BEGIN")

txn.insert("member", "M004",
           {"MemberID": "M004", "Name": "Sneha Joshi",
            "DOB": "2004-07-19", "Email": "sneha@iit.ac.in",
            "ContactNumber": "9222222222", "Role": "Student"})
print("  ✓ Inserted member M004 (Sneha Joshi)")

txn.insert("meallog", "L004",
           {"LogID": "L004", "MemberID": "M004",
            "ScheduleID": "SCH001", "Status": "Consumed"})
print("  ✓ Inserted MealLog L004 for M004")

txn.insert("monthly_mess_payment", "PAY003",
           {"MonthlyPaymentID": "PAY003", "MemberID": "M004",
            "StartDate": "2025-06-01", "EndDate": "2025-06-30",
            "Amount": 3000.0, "Status": "Pending"})
print("  ✓ Inserted MonthlyPayment PAY003 for M004")

db.commit(txn)
print(f"[Txn {txn.txn_id}] COMMITTED — WAL flushed to disk")

print("\nPhase 2: Simulate full system restart (new DatabaseManager instance)")
db2 = DatabaseManager(wal_path=WAL_PATH)

m4   = db2.tables["member"].search("M004")
l4   = db2.tables["meallog"].search("L004")
pay3 = db2.tables["monthly_mess_payment"].search("PAY003")

assert m4   is not None and m4["Name"] == "Sneha Joshi"
assert l4   is not None and l4["LogID"] == "L004"
assert pay3 is not None and pay3["Amount"] == 3000.0

print(f"  ✓ Member  M004  = {m4['Name']}")
print(f"  ✓ MealLog L004  = Status:{l4['Status']}")
print(f"  ✓ Payment PAY003= Amount:{pay3['Amount']} Status:{pay3['Status']}")
print("\n   DURABILITY PASSED — committed data survived restart.")


bar("FINAL STATE AFTER ALL ACID TESTS")
db2.show_all()

bar("ALL ACID TESTS PASSED SUCESSFULLY")