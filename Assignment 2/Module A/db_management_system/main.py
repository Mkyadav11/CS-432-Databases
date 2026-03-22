from database.bplustree import BPlusTree

tree=BPlusTree(order=4)
for key in [10,20,5,6,12,30,7,17,25,3,15,22]:
    tree.insert(key)
print(tree.search(15))
print(tree.search(99))
print(tree.range_query(6,20))
tree.delete(15)
print(tree.search(15))