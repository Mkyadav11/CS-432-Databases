class BPlusTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.children = []
        self.next = None  # For leaf node linking


class BPlusTree:
    def __init__(self, order=3):
        self.root = BPlusTreeNode(True)
        self.order = order

    def search(self, key, node=None):
        if node is None:
            node = self.root

        if node.leaf:
            return key in node.keys

        for i, k in enumerate(node.keys):
            if key < k:
                return self.search(key, node.children[i])
        return self.search(key, node.children[-1])

    def insert(self, key):
        root = self.root

        if len(root.keys) == (self.order - 1):
            new_root = BPlusTreeNode(False)
            new_root.children.append(self.root)
            self.split_child(new_root, 0)
            self.root = new_root

        self._insert_non_full(self.root, key)

    def _insert_non_full(self, node, key):
        if node.leaf:
            node.keys.append(key)
            node.keys.sort()
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

        self._insert_non_full(node.children[i], key)

    def split_child(self, parent, index):
        node = parent.children[index]
        new_node = BPlusTreeNode(node.leaf)
        mid = len(node.keys) // 2

        if node.leaf:
            new_node.keys = node.keys[mid:]
            node.keys = node.keys[:mid]
            parent.keys.insert(index, new_node.keys[0])
            new_node.next = node.next
            node.next = new_node
        else:
            parent.keys.insert(index, node.keys[mid])
            new_node.keys = node.keys[mid + 1:]
            node.keys = node.keys[:mid]
            new_node.children = node.children[mid + 1:]
            node.children = node.children[:mid + 1]

        parent.children.insert(index + 1, new_node)

    def range_query(self, start, end):
        node = self.root

        while not node.leaf:
            i = 0
            while i < len(node.keys) and start > node.keys[i]:
                i += 1
            node = node.children[i]

        result = []
        while node:
            for key in node.keys:
                if key > end:
                    return result
                if start <= key:
                    result.append(key)
            node = node.next

        return result

    def min_keys(self):
        import math
        return math.ceil((self.order - 1) / 2)

    def delete(self, key):
        self._delete(self.root, key)

        # If root becomes empty after merge, promote only child
        if not self.root.leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]

    def _delete(self, node, key):
        if node.leaf:
            if key in node.keys:
                node.keys.remove(key)
            return
        idx = 0
        while idx < len(node.keys) and key > node.keys[idx]:
            idx += 1

        child = node.children[idx]
        self._delete(child, key)

        if idx < len(node.keys) and node.keys[idx] == key:
            node.keys[idx] = self._get_leftmost_leaf_key(node.children[idx + 1])

        # Handle underflow after deletion
        if len(child.keys) < self.min_keys():
            self.fix_underflow(node, idx)

    def _get_leftmost_leaf_key(self, node):
        """Walk down to the leftmost leaf and return its first key."""
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]

    def fix_underflow(self, parent, idx):
        child = parent.children[idx]

        # Try LEFT sibling first
        if idx > 0:
            left = parent.children[idx - 1]
            if len(left.keys) > self.min_keys():
                self.borrow_from_left(parent, idx)
                return

        # Try RIGHT sibling
        if idx < len(parent.children) - 1:
            right = parent.children[idx + 1]
            if len(right.keys) > self.min_keys():
                self.borrow_from_right(parent, idx)
                return

        # Merge if neither sibling can lend
        if idx > 0:
            self.merge(parent, idx - 1)
        else:
            self.merge(parent, idx)

    def borrow_from_left(self, parent, idx):
        child = parent.children[idx]
        left = parent.children[idx - 1]

        if child.leaf:
            child.keys.insert(0, left.keys.pop())
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
            left.next = right.next
        else:
            left.keys.append(parent.keys[idx])
            left.keys.extend(right.keys)
            left.children.extend(right.children)

        parent.keys.pop(idx)
        parent.children.pop(idx + 1)