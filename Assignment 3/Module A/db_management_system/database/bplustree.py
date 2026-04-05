class BPlusTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.values = []     # parallel list to keys, only used in leaf nodes
        self.children = []
        self.next = None

    def __repr__(self):
        return f"BPlusTreeNode(leaf={self.leaf}, keys={self.keys})"


class BPlusTree:
    def __init__(self, order=3):
        self.root = BPlusTreeNode(True)
        self.order = order

    # ---------- search ----------
    def search(self, key, node=None):
        """Return the record (value) for key, or None if not found."""
        if node is None:
            node = self.root

        if node.leaf:
            for i, k in enumerate(node.keys):
                if k == key:
                    return node.values[i]   # ← return record, not True
            return None                     # ← not found → None

        for i, k in enumerate(node.keys):
            if key < k:
                return self.search(key, node.children[i])
        return self.search(key, node.children[-1])

    # ---------- insert ----------
    def insert(self, key, value):           # ← value param added
        root = self.root

        # Update existing key in-place
        existing = self.search(key)
        if existing is not None:
            leaf = self._find_leaf(key)
            leaf.values[leaf.keys.index(key)] = value
            return

        if len(root.keys) == (self.order - 1):
            new_root = BPlusTreeNode(False)
            new_root.children.append(self.root)
            self.split_child(new_root, 0)
            self.root = new_root

        self._insert_non_full(self.root, key, value)

    def _find_leaf(self, key, node=None):
        """Walk to the leaf that would contain key."""
        if node is None:
            node = self.root
        if node.leaf:
            return node
        for i, k in enumerate(node.keys):
            if key < k:
                return self._find_leaf(key, node.children[i])
        return self._find_leaf(key, node.children[-1])

    def _insert_non_full(self, node, key, value):   # ← value added
        if node.leaf:
            # Insert key+value together, keeping keys sorted
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            node.keys.insert(i, key)
            node.values.insert(i, value)            # ← keep values in sync
            return

        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if i >= len(node.children):
            i = len(node.children) - 1

        if len(node.children[i].keys) == (self.order - 1):
            self.split_child(node, i)
            if key > node.keys[i]:
                i += 1

        self._insert_non_full(node.children[i], key, value)

    def split_child(self, parent, index):
        node = parent.children[index]
        new_node = BPlusTreeNode(node.leaf)
        mid = len(node.keys) // 2

        if node.leaf:
            new_node.keys = node.keys[mid:]
            new_node.values = node.values[mid:]     # ← split values too
            node.keys = node.keys[:mid]
            node.values = node.values[:mid]         # ← trim values too
            parent.keys.insert(index, new_node.keys[0])
            new_node.next = node.next
            node.next = new_node
        else:
            parent.keys.insert(index, node.keys[mid])
            new_node.keys = node.keys[mid + 1:]
            node.keys = node.keys[:mid]
            new_node.children = node.children[mid + 1:]
            node.children = node.children[:mid + 1]
            # internal nodes don't store values, nothing extra needed

        parent.children.insert(index + 1, new_node)

    # ---------- delete (unchanged structurally) ----------
    def delete(self, key):
        self._delete(self.root, key)
        if not self.root.leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]

    def _delete(self, node, key):
        if node.leaf:
            if key in node.keys:
                idx = node.keys.index(key)
                node.keys.remove(key)
                node.values.pop(idx)                # ← remove value too
            return

        idx = 0
        while idx < len(node.keys) and key > node.keys[idx]:
            idx += 1

        child = node.children[idx]
        self._delete(child, key)

        if idx < len(node.keys) and node.keys[idx] == key:
            node.keys[idx] = self._get_leftmost_leaf_key(node.children[idx + 1])

        if len(child.keys) < self.min_keys():
            self.fix_underflow(node, idx)

    def _get_leftmost_leaf_key(self, node):
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]

    def fix_underflow(self, parent, idx):
        child = parent.children[idx]

        if idx > 0:
            left = parent.children[idx - 1]
            if len(left.keys) > self.min_keys():
                self.borrow_from_left(parent, idx)
                return

        if idx < len(parent.children) - 1:
            right = parent.children[idx + 1]
            if len(right.keys) > self.min_keys():
                self.borrow_from_right(parent, idx)
                return

        if idx > 0:
            self.merge(parent, idx - 1)
        else:
            self.merge(parent, idx)

    def borrow_from_left(self, parent, idx):
        child = parent.children[idx]
        left = parent.children[idx - 1]

        if child.leaf:
            child.keys.insert(0, left.keys.pop())
            child.values.insert(0, left.values.pop())   # ← move value too
            parent.keys[idx - 1] = child.keys[0]
        else:
            child.keys.insert(0, parent.keys[idx - 1])
            parent.keys[idx - 1] = left.keys.pop()
            child.children.insert(0, left.children.pop())

    def borrow_from_right(self, parent, idx):
        child = parent.children[idx]
        right = parent.children[idx + 1]

        if child.leaf:
            child.keys.append(right.keys.pop(0))
            child.values.append(right.values.pop(0))    # ← move value too
            if right.keys:
                parent.keys[idx] = right.keys[0]
        else:
            child.keys.append(parent.keys[idx])
            parent.keys[idx] = right.keys.pop(0)
            child.children.append(right.children.pop(0))

    def merge(self, parent, idx):
        left = parent.children[idx]
        right = parent.children[idx + 1]

        if left.leaf:
            left.keys.extend(right.keys)
            left.values.extend(right.values)            # ← merge values too
            left.next = right.next
        else:
            left.keys.append(parent.keys[idx])
            left.keys.extend(right.keys)
            left.children.extend(right.children)

        parent.keys.pop(idx)
        parent.children.pop(idx + 1)

    # ---------- NEW: scan & snapshot helpers ----------
    def min_keys(self):
        import math
        return math.ceil((self.order - 1) / 2)

    def all_records(self):
        """Return all (key, value) pairs in sorted order via leaf scan."""
        records = []
        node = self.root
        while not node.leaf:
            node = node.children[0]
        while node:
            for k, v in zip(node.keys, node.values):
                records.append((k, v))
            node = node.next
        return records

    def range_query(self, start, end):
        """Return (key, value) pairs where start <= key <= end."""
        node = self.root
        while not node.leaf:
            i = 0
            while i < len(node.keys) and start > node.keys[i]:
                i += 1
            node = node.children[i]

        result = []
        while node:
            for k, v in zip(node.keys, node.values):
                if k > end:
                    return result
                if k >= start:
                    result.append((k, v))
            node = node.next
        return result

    def snapshot(self):
        """Return a plain dict of all key→value pairs (for WAL recovery)."""
        return {k: v for k, v in self.all_records()}

    def restore_from_snapshot(self, snap: dict):
        """Rebuild tree from a snapshot dict."""
        self.root = BPlusTreeNode(True)
        for k, v in sorted(snap.items()):
            self.insert(k, v)