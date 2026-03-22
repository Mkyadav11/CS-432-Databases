from database.table import Table
class Database:
    def __init__(self):
        self.tables = {}

    def create_table(self, name, index):
        self.tables[name] = Table(name, index)

    def insert(self, table_name, key):
        self.tables[table_name].insert(key)

    def search(self, table_name, key):
        return self.tables[table_name].search(key)