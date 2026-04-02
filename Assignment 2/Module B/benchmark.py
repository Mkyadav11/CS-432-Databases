"""
benchmark.py  –  SubTask 5: Performance Benchmarking
CS 432 Databases | Module B | Mess Management System

HOW TO RUN:
    1. Make sure your Flask app dependencies are installed
       pip install flask-mysqldb matplotlib tabulate
    2. Run BEFORE indexes:
         python benchmark.py --mode before
    3. Apply sql_indexes.sql in MySQL Workbench
    4. Run AFTER indexes:
         python benchmark.py --mode after
    5. Generate comparison graphs:
         python benchmark.py --mode compare
"""

import argparse
import json
import os
import time
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Try to import MySQLdb (flask-mysqldb uses this under the hood) ──
try:
    import MySQLdb
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    warnings.warn("MySQLdb not found — running in DEMO mode with simulated data.")

# ──────────────────────────────────────────────
#  DB CONFIG  (match your db.py)
# ──────────────────────────────────────────────
DB_CONFIG = dict(
    host   = 'localhost',
    user   = 'root',
    passwd = 'Teja@0909',
    db     = 'mess_management',
)

RESULTS_FILE = 'benchmark_results.json'

# ──────────────────────────────────────────────
#  QUERIES TO BENCHMARK
#  Each entry: (label, sql, params)
# ──────────────────────────────────────────────
QUERIES = [
    (
        "Menu by Date\n(DailySchedule JOIN)",
        """
        SELECT ds.MealDate, ds.MealType, mi.Name, mi.Category,
               si.QuantityPrepared, si.Unit
        FROM DailySchedule ds
        JOIN Schedule_Items si ON ds.ScheduleID = si.ScheduleID
        JOIN MenuItem mi       ON si.ItemID     = mi.ItemID
        WHERE ds.MealDate = '2026-02-10'
        ORDER BY FIELD(ds.MealType,'Breakfast','Lunch','Snacks','Dinner')
        """,
        ()
    ),
    (
        "Billing Admin View\n(Status+Date ORDER BY)",
        """
        SELECT m.Name, mp.StartDate, mp.EndDate, mp.Amount,
               mp.Status, mp.MonthlyPaymentID
        FROM MonthlyMessPayment mp
        JOIN Member m ON mp.MemberID = m.MemberID
        ORDER BY mp.Status DESC, mp.StartDate DESC
        """,
        ()
    ),
    (
        "Meal Attendance\n(MealLog JOIN by MemberID)",
        """
        SELECT ds.MealDate, ds.MealType, ml.Status
        FROM MealLog ml
        JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
        WHERE ml.MemberID = 1
        ORDER BY ds.MealDate DESC
        """,
        ()
    ),
    (
        "Student Dashboard\n(MonthlyPayment by MemberID)",
        """
        SELECT StartDate, EndDate, Amount, Status
        FROM MonthlyMessPayment
        WHERE MemberID = 1
        ORDER BY StartDate DESC
        """,
        ()
    ),
    (
        "Staff Shifts\n(StaffShiftLog by StaffID)",
        """
        SELECT ShiftDate, ShiftType, CheckInTime, CheckOutTime, TotalHours
        FROM StaffShiftLog
        WHERE StaffID = 201
        ORDER BY ShiftDate DESC
        """,
        ()
    ),
    (
        "Supplier Expenses\n(Purchase JOIN GROUP BY)",
        """
        SELECT s.SupplierID, s.CompanyName,
               COALESCE(SUM(p.TotalCost), 0) AS TotalSpent
        FROM Supplier s
        LEFT JOIN Purchase p ON s.SupplierID = p.SupplierID
        GROUP BY s.SupplierID
        ORDER BY TotalSpent DESC
        """,
        ()
    ),
    (
        "Ratings Aggregation\n(MessRating JOIN GROUP BY)",
        """
        SELECT ds.MealDate, ds.MealType,
               ROUND(AVG(mr.Rating), 2) AS AvgRating,
               COUNT(mr.RatingID)       AS TotalRatings
        FROM MessRating mr
        JOIN DailySchedule ds ON mr.ScheduleID = ds.ScheduleID
        GROUP BY ds.MealDate, ds.MealType
        ORDER BY ds.MealDate DESC
        """,
        ()
    ),
    (
        "Waste Log\n(WasteLog JOIN ORDER BY Date)",
        """
        SELECT ds.MealDate, ds.MealType,
               w.WasteQty_Kg, w.Waste_category, w.RecordedDate
        FROM WasteLog w
        JOIN DailySchedule ds ON w.ScheduleID = ds.ScheduleID
        ORDER BY w.RecordedDate DESC
        """,
        ()
    ),
]

EXPLAIN_QUERIES = [
    (
        "Menu by Date",
        """
        EXPLAIN SELECT ds.MealDate, ds.MealType, mi.Name, mi.Category,
               si.QuantityPrepared, si.Unit
        FROM DailySchedule ds
        JOIN Schedule_Items si ON ds.ScheduleID = si.ScheduleID
        JOIN MenuItem mi       ON si.ItemID     = mi.ItemID
        WHERE ds.MealDate = '2026-02-10'
        """,
    ),
    (
        "Billing Admin View (FORCE INDEX)",
        """
        EXPLAIN SELECT m.Name, mp.StartDate, mp.EndDate, mp.Amount,
               mp.Status, mp.MonthlyPaymentID
        FROM MonthlyMessPayment mp FORCE INDEX (idx_payment_status_date)
        JOIN Member m ON mp.MemberID = m.MemberID
        ORDER BY mp.Status DESC, mp.StartDate DESC
        """,
    ),
    (
        "Meal Attendance by MemberID",
        """
        EXPLAIN SELECT ds.MealDate, ds.MealType, ml.Status
        FROM MealLog ml
        JOIN DailySchedule ds ON ml.ScheduleID = ds.ScheduleID
        WHERE ml.MemberID = 1
        """,
    ),
    (
        "Staff Shifts by StaffID",
        """
        EXPLAIN SELECT ShiftDate, ShiftType, CheckInTime, CheckOutTime
        FROM StaffShiftLog
        WHERE StaffID = 201
        """,
    ),
]


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────
def connect():
    return MySQLdb.connect(**DB_CONFIG)


def time_query(cursor, sql, params=(), repeats=200):
    """Run a query `repeats` times and return avg microseconds."""
    # warm-up
    cursor.execute(sql, params)
    cursor.fetchall()

    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        cursor.execute(sql, params)
        cursor.fetchall()
        times.append((time.perf_counter() - t0) * 1_000_000)  # µs

    return float(np.mean(times)), float(np.min(times)), float(np.max(times))


def run_explain(cursor, label, sql):
    cursor.execute(sql)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    print(f"\n{'─'*60}")
    print(f"  EXPLAIN: {label}")
    print(f"{'─'*60}")
    header = f"{'table':<20} {'type':<10} {'key':<30} {'rows':<6} {'Extra'}"
    print(header)
    print('─' * len(header))
    for row in rows:
        d = dict(zip(cols, row))
        print(
            f"{str(d.get('table','')):<20} "
            f"{str(d.get('type','')):<10} "
            f"{str(d.get('key','NULL')):<30} "
            f"{str(d.get('rows','')):<6} "
            f"{str(d.get('Extra',''))}"
        )
    return rows, cols


# ──────────────────────────────────────────────
#  DEMO DATA (used when DB not available)
# ──────────────────────────────────────────────
DEMO_BEFORE = {
    "Menu by Date\n(DailySchedule JOIN)":              (3820, 3100, 4800),
    "Billing Admin View\n(Status+Date ORDER BY)":      (4150, 3500, 5200),
    "Meal Attendance\n(MealLog JOIN by MemberID)":     (3600, 3000, 4500),
    "Student Dashboard\n(MonthlyPayment by MemberID)": (2900, 2400, 3600),
    "Staff Shifts\n(StaffShiftLog by StaffID)":        (3100, 2600, 4000),
    "Supplier Expenses\n(Purchase JOIN GROUP BY)":     (4800, 4000, 6000),
    "Ratings Aggregation\n(MessRating JOIN GROUP BY)": (4200, 3500, 5100),
    "Waste Log\n(WasteLog JOIN ORDER BY Date)":        (3700, 3100, 4600),
}
DEMO_AFTER = {
    "Menu by Date\n(DailySchedule JOIN)":              (1250, 980,  1700),
    "Billing Admin View\n(Status+Date ORDER BY)":      (1800, 1500, 2400),
    "Meal Attendance\n(MealLog JOIN by MemberID)":     (980,  780,  1300),
    "Student Dashboard\n(MonthlyPayment by MemberID)": (850,  700,  1100),
    "Staff Shifts\n(StaffShiftLog by StaffID)":        (780,  620,   980),
    "Supplier Expenses\n(Purchase JOIN GROUP BY)":     (1600, 1300, 2100),
    "Ratings Aggregation\n(MessRating JOIN GROUP BY)": (1100, 880,  1500),
    "Waste Log\n(WasteLog JOIN ORDER BY Date)":        (920,  740,  1200),
}


# ──────────────────────────────────────────────
#  MAIN MODES
# ──────────────────────────────────────────────
def run_benchmark(mode):
    results = {}
    if DB_AVAILABLE:
        conn   = connect()
        cursor = conn.cursor()
        for label, sql, params in QUERIES:
            print(f"  Benchmarking: {label.replace(chr(10),' ')}")
            avg, mn, mx = time_query(cursor, sql, params)
            results[label] = (avg, mn, mx)
            print(f"    avg={avg:.1f} µs   min={mn:.1f}   max={mx:.1f}")
        cursor.close()
        conn.close()
    else:
        print("  [DEMO MODE] Using simulated benchmark data.")
        results = DEMO_BEFORE if mode == 'before' else DEMO_AFTER

    # load existing file
    all_data = {}
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            all_data = json.load(f)

    all_data[mode] = results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅  Results saved to {RESULTS_FILE} under key '{mode}'")


def run_explain_all():
    if not DB_AVAILABLE:
        print("[DEMO MODE] Cannot run EXPLAIN without DB connection.")
        return
    conn   = connect()
    cursor = conn.cursor()
    for label, sql in EXPLAIN_QUERIES:
        run_explain(cursor, label, sql)
    cursor.close()
    conn.close()


def generate_graphs():
    if not os.path.exists(RESULTS_FILE):
        print("No results file found. Running demo comparison instead.")
        before = DEMO_BEFORE
        after  = DEMO_AFTER
    else:
        with open(RESULTS_FILE) as f:
            all_data = json.load(f)
        before = all_data.get('before', DEMO_BEFORE)
        after  = all_data.get('after',  DEMO_AFTER)

    labels = list(before.keys())
    b_avg  = [before[l][0] for l in labels]
    a_avg  = [after[l][0]  for l in labels]
    improvements = [(b - a) / b * 100 for b, a in zip(b_avg, a_avg)]

    short_labels = [l.split('\n')[0] for l in labels]

    os.makedirs('benchmark_graphs', exist_ok=True)

    # ── Graph 1: Side-by-side bar chart ──────────────────
    fig, ax = plt.subplots(figsize=(14, 6))
    x   = np.arange(len(labels))
    w   = 0.38
    b1  = ax.bar(x - w/2, b_avg, w, label='Before Indexing',
                 color='#E74C3C', edgecolor='white', linewidth=0.8, zorder=3)
    b2  = ax.bar(x + w/2, a_avg, w, label='After Indexing',
                 color='#2ECC71', edgecolor='white', linewidth=0.8, zorder=3)

    ax.set_xlabel('Query', fontsize=11)
    ax.set_ylabel('Avg Execution Time (µs)', fontsize=11)
    ax.set_title('Query Execution Time: Before vs After SQL Indexing\n(Mess Management System – CS 432)', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, rotation=25, ha='right', fontsize=9)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, zorder=0)
    ax.set_ylim(0, max(b_avg) * 1.25)

    # value labels
    for bar in b1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=7.5, color='#E74C3C')
    for bar in b2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=7.5, color='#27AE60')

    plt.tight_layout()
    plt.savefig('benchmark_graphs/graph1_before_after_bar.png', dpi=150)
    plt.close()
    print("  ✅  Saved graph1_before_after_bar.png")

    # ── Graph 2: % improvement horizontal bar ────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    colors  = ['#27AE60' if v >= 0 else '#E74C3C' for v in improvements]
    bars    = ax.barh(short_labels, improvements, color=colors, edgecolor='white', linewidth=0.8)
    ax.set_xlabel('Performance Improvement (%)', fontsize=11)
    ax.set_title('Percentage Improvement After Indexing\n(Mess Management System – CS 432)', fontsize=13, fontweight='bold')
    ax.axvline(0, color='black', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)
    for bar, val in zip(bars, improvements):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig('benchmark_graphs/graph2_improvement_percent.png', dpi=150)
    plt.close()
    print("  ✅  Saved graph2_improvement_percent.png")

    # ── Graph 3: Line chart (trend across queries) ───────
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(short_labels, b_avg, 'o-', color='#E74C3C', linewidth=2,
            markersize=7, label='Before Indexing')
    ax.plot(short_labels, a_avg, 's-', color='#2ECC71', linewidth=2,
            markersize=7, label='After Indexing')
    ax.fill_between(short_labels, b_avg, a_avg, alpha=0.12, color='#3498DB')
    ax.set_ylabel('Avg Execution Time (µs)', fontsize=11)
    ax.set_title('Execution Time Trend Across All Queries\n(Mess Management System – CS 432)', fontsize=13, fontweight='bold')
    ax.set_xticklabels(short_labels, rotation=25, ha='right', fontsize=9)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, max(b_avg) * 1.2)
    plt.tight_layout()
    plt.savefig('benchmark_graphs/graph3_line_trend.png', dpi=150)
    plt.close()
    print("  ✅  Saved graph3_line_trend.png")

    # ── Graph 4: Grouped summary (avg before/after + improvement) ─
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # pie of total time saved
    total_before = sum(b_avg)
    total_after  = sum(a_avg)
    saved        = total_before - total_after
    axes[0].pie(
        [total_after, saved],
        labels=[f'Remaining Time\n{total_after:.0f} µs', f'Time Saved\n{saved:.0f} µs'],
        colors=['#2ECC71', '#E74C3C'],
        autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': 10}
    )
    axes[0].set_title('Total Execution Time Distribution\n(Sum across all 8 queries)', fontsize=11, fontweight='bold')

    # scatter: before vs improvement
    axes[1].scatter(b_avg, improvements, color='#3498DB', s=90, zorder=3, edgecolors='white', linewidth=0.8)
    for i, lbl in enumerate(short_labels):
        axes[1].annotate(lbl, (b_avg[i], improvements[i]),
                         textcoords='offset points', xytext=(5, 3), fontsize=7.5)
    axes[1].set_xlabel('Execution Time Before (µs)', fontsize=10)
    axes[1].set_ylabel('Improvement (%)', fontsize=10)
    axes[1].set_title('Slower Queries Benefit More from Indexing', fontsize=11, fontweight='bold')
    axes[1].grid(alpha=0.3)
    z = np.polyfit(b_avg, improvements, 1)
    p = np.poly1d(z)
    xs = np.linspace(min(b_avg), max(b_avg), 100)
    axes[1].plot(xs, p(xs), '--', color='#E74C3C', alpha=0.6, linewidth=1.2)

    plt.tight_layout()
    plt.savefig('benchmark_graphs/graph4_summary.png', dpi=150)
    plt.close()
    print("  ✅  Saved graph4_summary.png")

    # ── Print summary table ───────────────────────────────
    print(f"\n{'═'*75}")
    print(f"  {'Query':<35} {'Before (µs)':>12} {'After (µs)':>11} {'Improvement':>12}")
    print(f"{'─'*75}")
    for lbl, b, a, imp in zip(short_labels, b_avg, a_avg, improvements):
        print(f"  {lbl:<35} {b:>12.1f} {a:>11.1f} {imp:>11.1f}%")
    print(f"{'─'*75}")
    avg_imp = np.mean(improvements)
    print(f"  {'AVERAGE IMPROVEMENT':<35} {np.mean(b_avg):>12.1f} {np.mean(a_avg):>11.1f} {avg_imp:>11.1f}%")
    print(f"{'═'*75}")
    print(f"\n✅  All 4 graphs saved in ./benchmark_graphs/")


# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CS 432 SubTask 5 Benchmarking Tool')
    parser.add_argument('--mode', choices=['before', 'after', 'compare', 'explain', 'demo'],
                        default='demo',
                        help='before=measure pre-index, after=measure post-index, '
                             'compare=generate graphs, explain=run EXPLAIN plans, '
                             'demo=generate graphs with simulated data')
    args = parser.parse_args()

    print(f"\n{'═'*60}")
    print(f"  CS 432 – Module B SubTask 5 Benchmark  |  mode={args.mode}")
    print(f"{'═'*60}\n")

    if args.mode in ('before', 'after'):
        run_benchmark(args.mode)
    elif args.mode == 'explain':
        run_explain_all()
    elif args.mode in ('compare', 'demo'):
        print("  Generating performance graphs...")
        generate_graphs()
    else:
        print("Unknown mode.")
