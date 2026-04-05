"""
Database Manager — Mess Management System
==========================================
Tables (each backed by its own B+ Tree):
  member               – MemberID (PK), Name, DOB, Email, ContactNumber, Role
  meallog              – LogID (PK), MemberID (FK), ScheduleID (FK), Status
  monthly_mess_payment – MonthlyPaymentID (PK), MemberID (FK), StartDate,
                         EndDate, Amount, Status (Paid/Pending)

Constraints enforced before every COMMIT:
  • member.Role ∈ {'Student', 'Admin', 'Staff'}
  • meallog.Status ∈ {'Consumed', 'Missed'}
  • monthly_mess_payment.Status ∈ {'Paid', 'Pending'}
  • monthly_mess_payment.Amount > 0
  • meallog.MemberID must reference an existing member
  • monthly_mess_payment.MemberID must reference an existing member
"""

from database.bplustree import BPlusTree
from database.wal import WAL
from database.transaction_manager import TransactionManager, Transaction


# ── Constraint Validators ────────────────────────────────────────────────

VALID_ROLES   = {"Student", "Admin", "Staff"}
VALID_STATUS_MEAL    = {"Consumed", "Missed"}
VALID_STATUS_PAYMENT = {"Paid", "Pending"}


def validate_member(tree):
    for _, rec in tree.all_records():
        if rec["Role"] not in VALID_ROLES:
            raise ValueError(
                f"Constraint: Member {rec['MemberID']} has invalid Role '{rec['Role']}'")


def validate_meallog(meallog_tree, member_tree):
    for _, rec in meallog_tree.all_records():
        if rec["Status"] not in VALID_STATUS_MEAL:
            raise ValueError(
                f"Constraint: MealLog {rec['LogID']} has invalid Status '{rec['Status']}'")
        if member_tree.search(rec["MemberID"]) is None:
            raise ValueError(
                f"Constraint: MealLog {rec['LogID']} references non-existent MemberID {rec['MemberID']}")


def validate_payment(payment_tree, member_tree):
    for _, rec in payment_tree.all_records():
        if rec["Status"] not in VALID_STATUS_PAYMENT:
            raise ValueError(
                f"Constraint: Payment {rec['MonthlyPaymentID']} has invalid Status '{rec['Status']}'")
        if rec["Amount"] <= 0:
            raise ValueError(
                f"Constraint: Payment {rec['MonthlyPaymentID']} has non-positive Amount {rec['Amount']}")
        if member_tree.search(rec["MemberID"]) is None:
            raise ValueError(
                f"Constraint: Payment {rec['MonthlyPaymentID']} references non-existent MemberID {rec['MemberID']}")


# ── Database Manager ─────────────────────────────────────────────────────

class DatabaseManager:
    TABLE_NAMES = ["member", "meallog", "monthly_mess_payment"]

    def __init__(self, wal_path="wal.log"):
        self.tables = {name: BPlusTree(order=4) for name in self.TABLE_NAMES}
        self.wal    = WAL(wal_path)
        self.txn_manager = TransactionManager(self.tables, self.wal)
        self._recover()

    # ── Recovery ─────────────────────────────────────────────────────────

    def _recover(self):
        committed, incomplete = self.wal.recover(self.tables)
        if committed or incomplete:
            print(f"[Recovery] Committed  : {committed}")
            print(f"[Recovery] Rolled back: {incomplete}")
        else:
            print("[Recovery] Clean startup — no recovery needed.")

    # ── Transaction API ───────────────────────────────────────────────────

    def begin(self) -> Transaction:
        return self.txn_manager.begin()

    def commit(self, txn: Transaction):
        """Run constraint checks, then durably commit."""
        self._check_constraints()
        txn.commit()

    def rollback(self, txn: Transaction):
        txn.rollback()

    # ── Constraints ───────────────────────────────────────────────────────

    def _check_constraints(self):
        validate_member(self.tables["member"])
        validate_meallog(self.tables["meallog"], self.tables["member"])
        validate_payment(self.tables["monthly_mess_payment"], self.tables["member"])

    # ── Seed ─────────────────────────────────────────────────────────────

    def seed(self):
        """Load initial demo data in one transaction."""
        txn = self.begin()
        try:
            # Members
            for m in [
                {"MemberID": "M001", "Name": "Aarav Shah",
                 "DOB": "2003-05-12", "Email": "aarav@iit.ac.in",
                 "ContactNumber": "9876543210", "Role": "Student"},
                {"MemberID": "M002", "Name": "Priya Nair",
                 "DOB": "2002-11-23", "Email": "priya@iit.ac.in",
                 "ContactNumber": "9123456780", "Role": "Student"},
                {"MemberID": "M003", "Name": "Rajan Mehta",
                 "DOB": "1985-03-07", "Email": "rajan@iit.ac.in",
                 "ContactNumber": "9000000001", "Role": "Admin"},
            ]:
                txn.insert("member", m["MemberID"], m)

            # MealLog entries
            for log in [
                {"LogID": "L001", "MemberID": "M001",
                 "ScheduleID": "SCH001", "Status": "Consumed"},
                {"LogID": "L002", "MemberID": "M002",
                 "ScheduleID": "SCH001", "Status": "Missed"},
                {"LogID": "L003", "MemberID": "M001",
                 "ScheduleID": "SCH002", "Status": "Consumed"},
            ]:
                txn.insert("meallog", log["LogID"], log)

            # Monthly payments
            for pay in [
                {"MonthlyPaymentID": "PAY001", "MemberID": "M001",
                 "StartDate": "2025-06-01", "EndDate": "2025-06-30",
                 "Amount": 3000.0, "Status": "Paid"},
                {"MonthlyPaymentID": "PAY002", "MemberID": "M002",
                 "StartDate": "2025-06-01", "EndDate": "2025-06-30",
                 "Amount": 3000.0, "Status": "Pending"},
            ]:
                txn.insert("monthly_mess_payment", pay["MonthlyPaymentID"], pay)

            self.commit(txn)
            print("[Seed] Initial data committed successfully.")
        except Exception as e:
            self.rollback(txn)
            print(f"[Seed] Rolled back — {e}")

    # ── Display ───────────────────────────────────────────────────────────

    def show_table(self, name):
        print(f"\n{'─'*62}")
        print(f"  TABLE: {name.upper()}")
        print(f"{'─'*62}")
        records = self.tables[name].all_records()
        if not records:
            print("  (empty)")
        for _, rec in records:
            print(f"  {rec}")
        print(f"{'─'*62}")

    def show_all(self):
        for t in self.TABLE_NAMES:
            self.show_table(t)