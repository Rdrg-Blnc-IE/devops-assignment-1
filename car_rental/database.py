

def singleton(cls):
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper


@singleton
class DB:
    def __init__(self, a):
        # TODO: connection to database
        self.db = 'DATABASE'

    def save(self, table: str, data):
        # TODO: save to database, in different tables
        pass

    def load(self, parameters):
        # TODO: load vehicles from database with stated parameters
        pass