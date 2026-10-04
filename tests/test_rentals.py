"""
Tests for car_rental/rental.py (Rental, RentalStatus, RentalBuilder).

These tests target build()'s business logic in isolation: date validation,
required-field checks, status transitions, and total_price calculation.
The DB lookup (checking the car exists/is active) and the final save are
mocked, since that's an external dependency, not the logic under test.

Run with:
    pytest tests/test_rental.py -v
    pytest tests/test_rental.py --cov=car_rental.rental
"""

from datetime import date, timedelta

import pytest

from car_rental import rental
from car_rental.rental import Rental, RentalBuilder, RentalStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ACTIVE_CAR = {"reg_num": "1HGCM82633A004352", "status": "active", "daily_rate": 20.0}
MAINTENANCE_CAR = {"reg_num": "OTHERVIN0000000001", "status": "maintenance", "daily_rate": 15.0}


class FakeDB:
    """Stand-in for the real DB, so build() can be tested without SQLite."""

    def __init__(self, cars_by_reg_num: dict):
        self._cars = cars_by_reg_num

    def load_vehicles(self, parameters=None):
        reg_num = parameters.get("reg_num") if parameters else None
        car = self._cars.get(reg_num)
        return [car] if car else []


@pytest.fixture(autouse=True)
def _patch_db_and_save(monkeypatch):
    """Replace the DB lookup and Rental.save for every test in this file,
    so build()'s own validation logic is what's actually under test.
    """
    fake_db = FakeDB({
        ACTIVE_CAR["reg_num"]: ACTIVE_CAR,
        MAINTENANCE_CAR["reg_num"]: MAINTENANCE_CAR,
    })
    monkeypatch.setattr(rental, "DB", fake_db)
    monkeypatch.setattr(Rental, "save", lambda self: None, raising=False)
    yield


@pytest.fixture
def valid_builder() -> RentalBuilder:
    """A builder pre-filled with valid data for an active car."""
    return (
        RentalBuilder()
        .with_customer_id(1)
        .with_car_reg_num(ACTIVE_CAR["reg_num"])
        .with_start_date(date.today() + timedelta(days=1))
        .with_end_date(date.today() + timedelta(days=5))
    )


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

class TestRequiredFields:
    def test_missing_customer_id_raises(self):
        builder = (
            RentalBuilder()
            .with_car_reg_num(ACTIVE_CAR["reg_num"])
            .with_start_date(date.today() + timedelta(days=1))
            .with_end_date(date.today() + timedelta(days=5))
        )
        with pytest.raises(ValueError, match="customer_id"):
            builder.build()

    def test_missing_car_reg_num_raises(self):
        builder = (
            RentalBuilder()
            .with_customer_id(1)
            .with_start_date(date.today() + timedelta(days=1))
            .with_end_date(date.today() + timedelta(days=5))
        )
        with pytest.raises(ValueError, match="car_reg_num"):
            builder.build()

    def test_missing_dates_raises(self):
        builder = RentalBuilder().with_customer_id(1).with_car_reg_num(ACTIVE_CAR["reg_num"])
        with pytest.raises(ValueError, match="start_date"):
            builder.build()


# ---------------------------------------------------------------------------
# Date validation
# ---------------------------------------------------------------------------

class TestDateValidation:
    def test_end_date_not_a_date_object_raises(self, valid_builder):
        valid_builder.end_date = "2026-11-05"  # string, not a date
        with pytest.raises(ValueError, match="date objects"):
            valid_builder.build()

    def test_end_date_equal_to_start_date_raises(self, valid_builder):
        same_day = date.today() + timedelta(days=1)
        valid_builder.with_start_date(same_day).with_end_date(same_day)
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            valid_builder.build()

    def test_end_date_before_start_date_raises(self, valid_builder):
        valid_builder.with_start_date(date.today() + timedelta(days=5))
        valid_builder.with_end_date(date.today() + timedelta(days=1))
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            valid_builder.build()

    def test_start_date_in_the_past_raises(self, valid_builder):
        valid_builder.with_start_date(date.today() - timedelta(days=1))
        with pytest.raises(ValueError, match="cannot be in the past"):
            valid_builder.build()

    def test_start_date_today_is_allowed(self, valid_builder):
        valid_builder.with_start_date(date.today())
        valid_builder.with_end_date(date.today() + timedelta(days=2))
        rental = valid_builder.build()
        assert rental.start_date == date.today()


# ---------------------------------------------------------------------------
# Vehicle lookup / status
# ---------------------------------------------------------------------------

class TestVehicleLookup:
    def test_unknown_car_reg_num_raises(self, valid_builder):
        valid_builder.with_car_reg_num("DOES-NOT-EXIST")
        with pytest.raises(ValueError, match="No vehicle found"):
            valid_builder.build()

    def test_car_not_active_raises(self, valid_builder):
        valid_builder.with_car_reg_num(MAINTENANCE_CAR["reg_num"])
        with pytest.raises(ValueError, match="not active"):
            valid_builder.build()


# ---------------------------------------------------------------------------
# Successful build: price calculation, defaults
# ---------------------------------------------------------------------------

class TestSuccessfulBuild:
    def test_total_price_is_days_times_daily_rate(self, valid_builder):
        # ACTIVE_CAR daily_rate = 20.0, start +1 day, end +5 days -> 4 days
        rental = valid_builder.build()
        assert rental.total_price == 80.0

    def test_default_status_is_pending(self, valid_builder):
        rental = valid_builder.build()
        assert rental.status == RentalStatus.pending

    def test_explicit_status_is_respected(self, valid_builder):
        valid_builder.with_status("confirmed")
        rental = valid_builder.build()
        assert rental.status == RentalStatus.confirmed

    def test_build_returns_rental_with_expected_fields(self, valid_builder):
        rental = valid_builder.build()
        assert rental.customer_id == 1
        assert rental.car_reg_num == ACTIVE_CAR["reg_num"]

    def test_single_day_rental_price(self, valid_builder):
        valid_builder.with_start_date(date.today() + timedelta(days=1))
        valid_builder.with_end_date(date.today() + timedelta(days=2))
        rental = valid_builder.build()
        assert rental.total_price == 20.0  # 1 day * 20.0


# ---------------------------------------------------------------------------
# RentalStatus enum
# ---------------------------------------------------------------------------

class TestRentalStatusEnum:
    def test_invalid_status_string_raises(self):
        with pytest.raises(ValueError):
            RentalBuilder().with_status("completed")  # not a real enum value, "returned" is

    def test_valid_statuses_accepted(self):
        for value in ("pending", "confirmed", "active", "returned", "canceled"):
            builder = RentalBuilder().with_status(value)
            assert builder.status == RentalStatus(value)

    def test_status_str_returns_plain_value(self):
        assert str(RentalStatus.confirmed) == "confirmed"