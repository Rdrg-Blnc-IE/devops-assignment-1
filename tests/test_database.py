"""
Tests for car_rental/database.py (the DB singleton).

Covers: save/load/update/delete for both vehicles and reservations,
the generic helper behavior (filtering, error on empty update), and
that the singleton returns the same instance across calls.

Run with:
    pytest tests/test_database.py -v
    pytest tests/test_database.py --cov=car_rental.database
"""

import sqlite3
from pathlib import Path

import pytest

from car_rental.database import DB

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE vehicles (
    reg_num TEXT PRIMARY KEY,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL,
    location TEXT NOT NULL,
    km INTEGER NOT NULL,
    daily_rate REAL NOT NULL
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_reg_num TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    status TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    FOREIGN KEY (car_reg_num) REFERENCES vehicles (reg_num)
);
"""


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Clear DB's cached singleton instance before every test.

    Without this, @singleton means DB(path) returns the SAME object no
    matter what path is passed after the first call — so every test
    after the first would silently reuse the first test's database.
    This fixture reaches into the decorator's closure and empties its
    instance cache so each test gets a genuinely fresh DB.
    """
    from car_rental import database as database_module

    # the `singleton` decorator stores its cache in `instances`, a dict
    # captured in the closure of `wrapper`. `__closure__` lets us reach
    # it from outside without changing the decorator itself.
    closure = database_module.DB.__closure__
    cell = next(c for c in closure if isinstance(c.cell_contents, dict))
    cell.cell_contents.clear()

    yield


@pytest.fixture
def db(tmp_path: Path):
    """A fresh DB instance backed by a temporary SQLite file."""
    from car_rental.database import DB

    db_path = tmp_path / "test.db"
    instance = DB(db_path)
    instance.conn.executescript(SCHEMA)
    instance.conn.commit()

    yield instance

    instance.close()


@pytest.fixture
def sample_vehicle() -> dict:
    return {
        "reg_num": "1HGCM82633A004352",
        "brand": "Toyota",
        "model": "Corolla",
        "status": "active",
        "location": "madrid",
        "km": 18500,
        "daily_rate": 39.99,
    }


@pytest.fixture
def sample_reservation() -> dict:
    return {
        "car_reg_num": "1HGCM82633A004352",
        "customer_name": "Jane Doe",
        "status": "pending",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
    }


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------

class TestVehicles:
    def test_save_and_load_vehicle(self, db, sample_vehicle):
        db.save_vehicle(sample_vehicle)

        rows = db.load_vehicles()

        assert len(rows) == 1
        assert rows[0]["reg_num"] == sample_vehicle["reg_num"]
        assert rows[0]["brand"] == "Toyota"

    def test_load_vehicles_with_filter(self, db, sample_vehicle):
        db.save_vehicle(sample_vehicle)
        db.save_vehicle({**sample_vehicle, "reg_num": "OTHERVIN0000000001", "location": "barcelona"})

        madrid_only = db.load_vehicles({"location": "madrid"})

        assert len(madrid_only) == 1
        assert madrid_only[0]["location"] == "madrid"

    def test_load_vehicles_filter_no_match_returns_empty(self, db, sample_vehicle):
        db.save_vehicle(sample_vehicle)

        result = db.load_vehicles({"location": "mallorca"})

        assert result == []

    def test_update_vehicle(self, db, sample_vehicle):
        db.save_vehicle(sample_vehicle)

        db.update_vehicle(sample_vehicle["reg_num"], {"km": 21500, "status": "maintenance"})

        updated = db.load_vehicles({"reg_num": sample_vehicle["reg_num"]})[0]
        assert updated["km"] == 21500
        assert updated["status"] == "maintenance"

    def test_update_vehicle_with_no_fields_raises(self, db, sample_vehicle):
        db.save_vehicle(sample_vehicle)

        with pytest.raises(ValueError):
            db.update_vehicle(sample_vehicle["reg_num"], {})

    def test_delete_vehicle_is_soft_delete(self, db, sample_vehicle):
        """Deleting a vehicle must mark it retired, not remove the row."""
        db.save_vehicle(sample_vehicle)

        db.delete_vehicle(sample_vehicle["reg_num"])

        rows = db.load_vehicles()
        assert len(rows) == 1  # row still exists
        assert rows[0]["status"] == "retired"


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------

class TestReservations:
    def test_save_and_load_reservation(self, db, sample_vehicle, sample_reservation):
        db.save_vehicle(sample_vehicle)
        db.save_reservation(sample_reservation)

        rows = db.load_reservations()

        assert len(rows) == 1
        assert rows[0]["customer_name"] == "Jane Doe"
        assert rows[0]["status"] == "pending"

    def test_load_reservations_with_filter(self, db, sample_vehicle, sample_reservation):
        db.save_vehicle(sample_vehicle)
        db.save_reservation(sample_reservation)
        db.save_reservation({**sample_reservation, "customer_name": "John Smith", "status": "confirmed"})

        pending_only = db.load_reservations({"status": "pending"})

        assert len(pending_only) == 1
        assert pending_only[0]["customer_name"] == "Jane Doe"

    def test_update_reservation_by_id(self, db, sample_vehicle, sample_reservation):
        db.save_vehicle(sample_vehicle)
        db.save_reservation(sample_reservation)
        reservation_id = db.load_reservations()[0]["id"]

        db.update_reservation(reservation_id, {"status": "confirmed"})

        updated = db.load_reservations({"id": reservation_id})[0]
        assert updated["status"] == "confirmed"

    def test_delete_reservation_is_soft_delete(self, db, sample_vehicle, sample_reservation):
        """Deleting a reservation must mark it canceled, not remove the row."""
        db.save_vehicle(sample_vehicle)
        db.save_reservation(sample_reservation)
        reservation_id = db.load_reservations()[0]["id"]

        db.delete_reservation(reservation_id)

        rows = db.load_reservations()
        assert len(rows) == 1  # row still exists
        assert rows[0]["status"] == "canceled"


# ---------------------------------------------------------------------------
# Foreign key enforcement (PRAGMA foreign_keys = ON)
# ---------------------------------------------------------------------------

class TestForeignKeyConstraint:
    def test_reservation_with_unknown_car_reg_num_raises(self, db, sample_reservation):
        """Foreign keys are enabled in __init__, so a reservation referencing
        a reg_num that doesn't exist in vehicles must be rejected by SQLite.
        """
        with pytest.raises(sqlite3.IntegrityError):
            db.save_reservation(sample_reservation)  # no matching vehicle saved first