"""
Write-Ahead Log (WAL) — provides Atomicity + Durability.

Every operation is logged to disk (fsync) BEFORE it is applied.
On restart, REDO committed transactions and UNDO incomplete ones.
"""

import json
import os
import threading


class WAL:
    def __init__(self, log_path="wal.log"):
        self.log_path = log_path
        self._lock = threading.Lock()
        self._lsn = 0
        self._load_lsn()

    # ── Writing ─────────────────────────────────────────────────────────

    def _next_lsn(self):
        self._lsn += 1
        return self._lsn

    def _append(self, record: dict):
        record["lsn"] = self._next_lsn()
        with self._lock:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(record) + "\n")
                f.flush()
                os.fsync(f.fileno())

    def log_begin(self, txn_id):
        self._append({"txn_id": txn_id, "type": "BEGIN",
                      "table": None, "key": None,
                      "old_value": None, "new_value": None})

    def log_update(self, txn_id, table, key, old_value, new_value):
        self._append({"txn_id": txn_id, "type": "UPDATE",
                      "table": table, "key": key,
                      "old_value": old_value, "new_value": new_value})

    def log_commit(self, txn_id):
        self._append({"txn_id": txn_id, "type": "COMMIT",
                      "table": None, "key": None,
                      "old_value": None, "new_value": None})

    def log_rollback(self, txn_id):
        self._append({"txn_id": txn_id, "type": "ROLLBACK",
                      "table": None, "key": None,
                      "old_value": None, "new_value": None})

    # ── Reading ──────────────────────────────────────────────────────────

    def read_all(self):
        if not os.path.exists(self.log_path):
            return []
        records = []
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records

    def _load_lsn(self):
        records = self.read_all()
        if records:
            self._lsn = max(r.get("lsn", 0) for r in records)

    def truncate(self):
        with self._lock:
            open(self.log_path, "w").close()
        self._lsn = 0

    # ── Recovery (ARIES-simplified) ──────────────────────────────────────

    def recover(self, tables: dict):
        records = self.read_all()
        if not records:
            return set(), set()

        started, committed, rolled_back = set(), set(), set()
        for r in records:
            t, tid = r["type"], r["txn_id"]
            if t == "BEGIN":    started.add(tid)
            elif t == "COMMIT": committed.add(tid)
            elif t == "ROLLBACK": rolled_back.add(tid)

        incomplete = started - committed - rolled_back

        # REDO committed
        for r in records:
            if r["type"] == "UPDATE" and r["txn_id"] in committed:
                tbl = r["table"]
                if tbl in tables:
                    if r["new_value"] is not None:
                        tables[tbl].insert(r["key"], r["new_value"])
                    else:
                        tables[tbl].delete(r["key"])

        # UNDO incomplete (reverse order)
        for r in reversed(records):
            if r["type"] == "UPDATE" and r["txn_id"] in incomplete:
                tbl = r["table"]
                if tbl in tables:
                    if r["old_value"] is not None:
                        tables[tbl].insert(r["key"], r["old_value"])
                    else:
                        tables[tbl].delete(r["key"])

        for tid in incomplete:
            self.log_rollback(tid)

        return committed, incomplete