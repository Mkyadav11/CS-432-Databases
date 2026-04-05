import random
import time
import sys
import matplotlib.pyplot as plt
from database.bplustree import BPlusTree
from database.bruteforce import BruteForceDB

# CONFIG 
SIZES = [100, 500, 1000, 5000, 10000, 50000]
NUM_BENCHMARK_RUNS = 5    
NUM_RANGE_TRIALS   = 10     
TREE_ORDER         = 50    
NUM_RANDOM_OPS     = 1000   


#  MEMORY HELPER 
def deep_size(obj, seen=None, depth=0):
    if seen is None:
        seen = set()
    if depth > 15:
        return 0

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        for k, v in obj.items():
            size += deep_size(k, seen, depth + 1)
            size += deep_size(v, seen, depth + 1)

    elif hasattr(obj, '__dict__'):
        for key, value in vars(obj).items():
            if key == "next":   # avoid leaf chain recursion
                size += sys.getsizeof(value) if value is not None else 0
                continue
            size += deep_size(value, seen, depth + 1)

    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            size += deep_size(item, seen, depth + 1)

    return size


insert_bpt,  insert_bf  = [], []
search_bpt,  search_bf  = [], []
delete_bpt,  delete_bf  = [], []
range_bpt,   range_bf   = [], []
random_bpt,  random_bf  = [], []
memory_bpt,  memory_bf  = [], []


# MAIN BENCHMARK LOOP
for size in SIZES:
    print(f"\n{'='*50}")
    print(f"  Benchmarking size = {size}  ({NUM_BENCHMARK_RUNS} runs each)")
    print(f"{'='*50}")

    data = random.sample(range(1, 1_000_000), size)

    # Accumulators for this size across all runs
    ins_bpt_runs,  ins_bf_runs  = [], []
    srch_bpt_runs, srch_bf_runs = [], []
    del_bpt_runs,  del_bf_runs  = [], []
    rng_bpt_runs,  rng_bf_runs  = [], []
    rnd_bpt_runs,  rnd_bf_runs  = [], []

    for run in range(NUM_BENCHMARK_RUNS):

        # Fresh structures each run
        bpt = BPlusTree(order=TREE_ORDER)
        bf  = BruteForceDB()

        # INSERTION 
        t = time.perf_counter()
        for x in data:
            bpt.insert(x)
        ins_bpt_runs.append(time.perf_counter() - t)

        t = time.perf_counter()
        for x in data:
            bf.insert(x)
        ins_bf_runs.append(time.perf_counter() - t)

        # Sort BF data once so range query can short-circuit
        bf.data.sort()

    # SEARCH    
        queries = random.choices(data, k=5000)

        t = time.perf_counter()
        for q in queries:
            bpt.search(q)
        srch_bpt_runs.append(time.perf_counter() - t)

        t = time.perf_counter()
        for q in queries:
            bf.search(q)
        srch_bf_runs.append(time.perf_counter() - t)

        #  DELETION 
        delete_data = random.sample(data, min(1000, size))

        t = time.perf_counter()
        for d in delete_data:
            bpt.delete(d)
        del_bpt_runs.append(time.perf_counter() - t)

        t = time.perf_counter()
        for d in delete_data:
            bf.delete(d)
        del_bf_runs.append(time.perf_counter() - t)

        #  RANGE QUERY 
        data_min, data_max = min(data), max(data)
        span = max(1, (data_max - data_min) // 20)  # 5% window

        bpt_rng_trial, bf_rng_trial = 0.0, 0.0
        for _ in range(NUM_RANGE_TRIALS):
            rs = random.randint(data_min, data_max - span)
            re = rs + span

            t = time.perf_counter()
            bpt.range_query(rs, re)
            bpt_rng_trial += time.perf_counter() - t

            t = time.perf_counter()
            bf.range_query(rs, re)
            bf_rng_trial += time.perf_counter() - t

        rng_bpt_runs.append(bpt_rng_trial / NUM_RANGE_TRIALS)
        rng_bf_runs.append(bf_rng_trial  / NUM_RANGE_TRIALS)

        # RANDOM MIXED OPERATIONS 
        bpt_rand = BPlusTree(order=TREE_ORDER)
        bf_rand  = BruteForceDB()
        seed_data = random.sample(data, size // 2)
        for x in seed_data:
            bpt_rand.insert(x)
            bf_rand.insert(x)

        # a mixed op sequence: 50% insert, 30% search, 20% delete
        ops = (
            [('insert', random.randint(1, 1_000_000)) for _ in range(NUM_RANDOM_OPS // 2)] +
            [('search', random.choice(seed_data))     for _ in range(int(NUM_RANDOM_OPS * 0.3))] +
            [('delete', random.choice(seed_data))     for _ in range(int(NUM_RANDOM_OPS * 0.2))]
        )
        random.shuffle(ops)

        t = time.perf_counter()
        for op, key in ops:
            if op == 'insert':
                bpt_rand.insert(key)
            elif op == 'search':
                bpt_rand.search(key)
            else:
                bpt_rand.delete(key)
        rnd_bpt_runs.append(time.perf_counter() - t)

        t = time.perf_counter()
        for op, key in ops:
            if op == 'insert':
                bf_rand.insert(key)
            elif op == 'search':
                bf_rand.search(key)
            else:
                bf_rand.delete(key)
        rnd_bf_runs.append(time.perf_counter() - t)

    # AVERAGE ACROSS RUNS 
    def avg(lst): return sum(lst) / len(lst)

    insert_bpt.append(avg(ins_bpt_runs))
    insert_bf.append(avg(ins_bf_runs))
    search_bpt.append(avg(srch_bpt_runs))
    search_bf.append(avg(srch_bf_runs))
    delete_bpt.append(avg(del_bpt_runs))
    delete_bf.append(avg(del_bf_runs))
    range_bpt.append(avg(rng_bpt_runs))
    range_bf.append(avg(rng_bf_runs))
    random_bpt.append(avg(rnd_bpt_runs))
    random_bf.append(avg(rnd_bf_runs))

    # Memory measured once on a freshly populated structure (not after deletions)
    bpt_mem = BPlusTree(order=TREE_ORDER)
    bf_mem  = BruteForceDB()
    for x in data:
        bpt_mem.insert(x)
        bf_mem.insert(x)
    memory_bpt.append(deep_size(bpt_mem))
    memory_bf.append(deep_size(bf_mem))

    print(f"  Insert  : BPT={insert_bpt[-1]*1000:.3f}ms   BF={insert_bf[-1]*1000:.3f}ms")
    print(f"  Search  : BPT={search_bpt[-1]*1000:.3f}ms   BF={search_bf[-1]*1000:.3f}ms")
    print(f"  Delete  : BPT={delete_bpt[-1]*1000:.3f}ms   BF={delete_bf[-1]*1000:.3f}ms")
    print(f"  Range   : BPT={range_bpt[-1]*1000:.3f}ms   BF={range_bf[-1]*1000:.3f}ms")
    print(f"  Random  : BPT={random_bpt[-1]*1000:.3f}ms   BF={random_bf[-1]*1000:.3f}ms")
    print(f"  Memory  : BPT={memory_bpt[-1]//1024}KB   BF={memory_bf[-1]//1024}KB")


# PLOT 
def plot_graph(x, y1, y2, title, ylabel="Time (s)"):
    plt.figure(figsize=(7, 4))
    plt.plot(x, y1, marker='o', linewidth=2, label="B+ Tree")
    plt.plot(x, y2, marker='s', linewidth=2, label="Brute Force")
    plt.xlabel("Data Size")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()


plot_graph(SIZES, insert_bpt,  insert_bf,  "Insertion Time (avg over 5 runs)")
plot_graph(SIZES, search_bpt,  search_bf,  "Search Time (avg over 5 runs)")
plot_graph(SIZES, delete_bpt,  delete_bf,  "Deletion Time (avg over 5 runs)")
plot_graph(SIZES, range_bpt,   range_bf,   "Range Query Time (avg over 5 runs)")
plot_graph(SIZES, random_bpt,  random_bf,  "Random Mixed Operations Time")
plot_graph(SIZES, memory_bpt,  memory_bf,  "Memory Usage", ylabel="Memory (bytes)")

plt.show()