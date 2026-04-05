class Table:
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def insert(self, key):
        self.index.insert(key)

    def search(self, key):
        return self.index.search(key)