# memory_store.py
class ClauseMemory:
    def __init__(self):
        self.clauses = []

    def store(self, new_clauses):
        self.clauses = new_clauses

    def get_all(self):
        return self.clauses

    def is_empty(self):
        return len(self.clauses) == 0


clause_memory = ClauseMemory()
