class BruteForceDB:
    def __init__(self):
        self.data = []

    # INSERT
    def insert(self, key):
        if key not in self.data:   # O(n)
            self.data.append(key)

    # SEARCH
    def search(self, key):
        return key in self.data

    # DELETE
    def delete(self, key):
        if key in self.data:
            self.data.remove(key)

    # RANGE QUERY
    def range_query(self, start, end):
        result = []
        for x in self.data:
            if x > end:
                break
            if x >= start:
                result.append(x)
        return result