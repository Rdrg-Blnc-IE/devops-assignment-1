import sqlite3
from pathlib import Path
from typing import Any, Optional


def singleton(cls):
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper


@singleton
class DB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # rows behave like dicts
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _save(self, table: str, data: dict[str, Any]) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())
        self.conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
        self.conn.commit()

    def _load(self, table: str, parameters: Optional[dict[str, Any]] = None) -> list[dict]:
        query = f"SELECT * FROM {table}"
        values = ()

        if parameters:
            conditions = " AND ".join(f"{key} = ?" for key in parameters)
            query += f" WHERE {conditions}"
            values = tuple(parameters.values())

        cur = self.conn.execute(query, values)
        return [dict(row) for row in cur.fetchall()]

    def _update(self, table: str, key_value, parameters: dict[str, Any], key_column: str) -> None:
        if not parameters:
            raise ValueError("update requires at least one field to change")

        assignments = ", ".join(f"{key} = ?" for key in parameters)
        values = tuple(parameters.values()) + (key_value,)

        self.conn.execute(f"UPDATE {table} SET {assignments} WHERE {key_column} = ?", values)
        self.conn.commit()

    # Vehicles — by reg_num

    def save_vehicle(self, data: dict[str, Any]) -> None:
        self._save("vehicles", data)

    def load_vehicles(self, parameters = None) -> list[dict]:
        return self._load("vehicles", parameters)

    def update_vehicle(self, reg_num: str, parameters: dict[str, Any]) -> None:
        self._update("vehicles", reg_num, parameters, key_column="reg_num")

    def delete_vehicle(self, reg_num: str) -> None:
        # soft-delete: mark the vehicle as retired rather than deleting the row
        self.update_vehicle(reg_num, {"status": "retired"})

    # Reservations — by id

    def save_reservation(self, data: dict[str, Any]) -> None:
        self._save("rentals", data)

    def load_reservations(self, parameters: Optional[dict[str, Any]] = None) -> list[dict]:
        return self._load("rentals", parameters)

    def update_reservation(self, reservation_id: int, parameters: dict[str, Any]) -> None:
        self._update("rentals", reservation_id, parameters, key_column="id")

    def delete_reservation(self, reservation_id: int) -> None:
        self._update("rentals", reservation_id, {"status": "canceled"}, key_column="id")

    # Customers — by id

    def load_customers(self, parameters: Optional[dict[str, Any]] = None) -> list[dict]:
        return self._load("customers", parameters)

    def get_customer_by_id(self, customer_id: int) -> Optional[dict]:
        res = self._load("customers", {"id": customer_id})
        return res[0] if res else None

    def close(self) -> None:
        self.conn.close()


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "src" / "vehicles.db"
db_instance = DB(DB_PATH)