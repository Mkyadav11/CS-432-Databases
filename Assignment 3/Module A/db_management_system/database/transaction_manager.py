"""
Transaction Manager — coordinates BEGIN / COMMIT / ROLLBACK.

Isolation: table-level exclusive locks (simple, serializable).
Atomicity: undo buffer applied in reverse on rollback.
"""

import threading
import uuid
import time
from database.wal import WAL


class Transaction:
    def __init__(self, txn_id, tables, wal, lock_manager):
        self.txn_id       = txn_id
        self.tables       = tables
        self.wal          = wal
        self.lock_manager = lock_manager
        self.undo_log     = []          # (table, key, old_value)
        self.active       = True
        self._locks       = []

    # ── DML ─────────────────────────────────────────────────────────────

    def insert(self, table, key, record):
        self._check(); self._lock(table)
        old = self._tree(table).search(key)
        self.undo_log.append((table, key, old))
        self.wal.log_update(self.txn_id, table, key, old, record)
        self._tree(table).insert(key, record)

    def update(self, table, key, new_record):
        self._check(); self._lock(table)
        old = self._tree(table).search(key)
        if old is None:
            raise KeyError(f"Key {key!r} not found in '{table}'")
        self.undo_log.append((table, key, old))
        self.wal.log_update(self.txn_id, table, key, old, new_record)
        self._tree(table).insert(key, new_record)

    def delete(self, table, key):
        self._check(); self._lock(table)
        old = self._tree(table).search(key)
        if old is None:
            raise KeyError(f"Key {key!r} not found in '{table}'")
        self.undo_log.append((table, key, old))
        self.wal.log_update(self.txn_id, table, key, old, None)
        self._tree(table).delete(key)

    def select(self, table, key):
        self._check(); self._lock(table)
        return self._tree(table).search(key)

    def scan(self, table):
        return self._tree(table).all_records()

    # ── Commit / Rollback ────────────────────────────────────────────────

    def commit(self):
        self._check()
        self.wal.log_commit(self.txn_id)
        self.active = False
        self._release()

    def rollback(self):
        for table, key, old_value in reversed(self.undo_log):
            tree = self.tables.get(table)
            if tree is None:
                continue
            if old_value is not None:
                tree.insert(key, old_value)
            else:
                tree.delete(key)
        self.wal.log_rollback(self.txn_id)
        self.active = False
        self._release()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _check(self):
        if not self.active:
            raise RuntimeError("Transaction is no longer active.")

    def _tree(self, name):
        if name not in self.tables:
            raise ValueError(f"Unknown table: '{name}'")
        return self.tables[name]

    def _lock(self, table):
        if table not in self._locks:
            self.lock_manager.acquire(table, self.txn_id)
            self._locks.append(table)

    def _release(self):
        for t in self._locks:
            self.lock_manager.release(t, self.txn_id)
        self._locks.clear()


# ── Lock Manager ─────────────────────────────────────────────────────────

class LockManager:
    def __init__(self):
        self._mu    = threading.Lock()
        self._locks = {}          # table → txn_id
        self._conds = {}          # table → Condition

    def acquire(self, table, txn_id, timeout=5.0):
        with self._mu:
            if table not in self._conds:
                self._conds[table] = threading.Condition(self._mu)
        cond = self._conds[table]
        with self._mu:
            deadline = time.time() + timeout
            while self._locks.get(table) not in (None, txn_id):
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(
                        f"Lock timeout on '{table}' for txn {txn_id}")
                cond.wait(timeout=remaining)
            self._locks[table] = txn_id

    def release(self, table, txn_id):
        with self._mu:
            if self._locks.get(table) == txn_id:
                del self._locks[table]
                cond = self._conds.get(table)
                if cond:
                    cond.notify_all()


# ── Transaction Manager ───────────────────────────────────────────────────

class TransactionManager:
    def __init__(self, tables: dict, wal: WAL):
        self.tables       = tables
        self.wal          = wal
        self.lock_manager = LockManager()

    def begin(self) -> Transaction:
        txn_id = str(uuid.uuid4())[:8]
        self.wal.log_begin(txn_id)
        return Transaction(txn_id, self.tables, self.wal, self.lock_manager)