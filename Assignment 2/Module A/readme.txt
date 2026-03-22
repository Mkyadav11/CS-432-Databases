# B+ Tree Database Management System

A from-scratch implementation of a B+ Tree data structure compared against a Brute Force (linear list) approach across four core database operations — insertion, search, deletion, and range queries. Includes automated benchmarking, performance visualisation using Matplotlib, and tree structure visualisation using Graphviz.

---

## Project Structure

```
db_management_system/
│
├── database/
│   ├── bplustree.py        # B+ Tree implementation
│   ├── bruteforce.py       # Brute Force baseline (plain Python list)
│   └── table.py            # Table wrapper used by Database manager
│
├── performance_test.py     # Benchmarking and Matplotlib plots
├── visualize.py            # Graphviz tree visualisation
└── README.md
```

---

## File Descriptions

### `database/bplustree.py`
Contains the full B+ Tree implementation with two classes:
- **BPlusTreeNode** — represents a single node, stores keys, children, and a `next` pointer for leaf linking
- **BPlusTree** — manages the full tree with the following methods:

| Method | Description | Time Complexity |
| `insert(key)` | Inserts a key, splits nodes when full | O(log n) |
| `search(key)` | Finds a key by traversing internal nodes | O(log n) |
| `delete(key)` | Removes a key, rebalances via borrow or merge | O(log n) |
| `range_query(start, end)` | Returns all keys in range using leaf linked list | O(log n + k) |

### `database/bruteforce.py`
A simple baseline that stores all keys in a plain Python list. Every operation scans the entire list linearly — O(n). Used purely for performance comparison.

### `database/table.py`
A thin wrapper that connects a table name to an index structure (either B+ Tree or Brute Force). Used by the Database manager class.

### `performance_test.py`
Runs automated benchmarks across six data sizes: **100, 500, 1000, 5000, 10000, 50000 keys**.
Each test is averaged over **5 runs** for stability. Measures and plots:
- Insertion time
- Search time
- Deletion time
- Range query time
- Random mixed operations time
- Memory usage

Generates **6 Matplotlib graphs** comparing B+ Tree vs Brute Force.

### `visualize.py`
Uses **Graphviz** to render the B+ Tree as a PNG image showing:
- Tree hierarchy — ROOT, INTERNAL, and LEAF nodes
- Parent-child relationships via solid arrows
- Leaf linked list via dashed arrows

---

## Requirements
Python Version
Python 3.7 or higher

Python Packages
Install all required packages using:
```bash
pip install graphviz matplotlib

Graphviz Software
The `visualize.py` file requires the Graphviz software to be installed on your system.


### 2. Run the Tree Visualisation
This will generate and open `sample_bplustree.png`:
python visualize.py


### 3. Use the B+ Tree Directly
Open a Python terminal in the project folder:
  python
from database.bplustree import BPlusTree

tree = BPlusTree(order=4)

# Insert keys
for key in [10, 20, 5, 6, 12, 30, 7, 17, 25, 3, 15, 22]:
    tree.insert(key)

# Search
print(tree.search(15))          # True
print(tree.search(99))          # False

# Range query
print(tree.range_query(6, 20))  # [6, 7, 10, 12, 15, 17, 20]

# Delete
tree.delete(15)
print(tree.search(15))          # False