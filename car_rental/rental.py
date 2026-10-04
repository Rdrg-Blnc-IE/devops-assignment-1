from dataclasses import dataclass, asdict
from datetime import date
from .database import db_instance as db
from .vehicle_info import StrValueEnum


class RentalStatus(StrValueEnum):
    pending = 'pending'      # created, not yet confirmed
    confirmed = 'confirmed'  # confirmed, car not yet picked up
    active = 'active'        # car picked up, currently rented
    returned = 'returned'    # car returned, rental complete
    canceled = 'canceled'    # canceled before or during the rental


@dataclass
class Rental:
    customer_id: int  # FK to a customer/user, e.g. 12
    car_reg_num: str  # FK to Vehicle.reg_num, e.g. "1HCM82633A004352"
    start_date: date  # e.g. date(2026, 11, 1)
    end_date: date  # e.g. date(2026, 11, 5)
    total_price: float  # e.g. 199.95
    status: RentalStatus  # RentalStatus.pending

def save(rental: Rental):
    data = asdict(rental)
    for k, val in data.items():
        if hasattr(val, 'value'):
            data[k] = val.value
        elif isinstance(val, date):
            data[k] = val.isoformat()
    db.save_vehicle(data)

def update(rental_id: int, parameters: dict):
        if rental_id:
            db.update_reservation(rental_id, parameters)
        else:
            raise ValueError("No rental_id provided")


class RentalBuilder:
    def __init__(self):
        self.customer_id = None
        self.car_reg_num = None
        self.start_date = None
        self.end_date = None
        self.total_price = None
        self.status = None

    def with_customer_id(self, customer_id: int):
        self.customer_id = customer_id
        return self

    def with_car_reg_num(self, car_reg_num: str):
        self.car_reg_num = car_reg_num
        return self

    def with_start_date(self, start_date: date):
        self.start_date = start_date
        return self

    def with_end_date(self, end_date: date):
        self.end_date = end_date
        return self

    def with_status(self, status: str):
        self.status = RentalStatus(status)
        return self

    def build(self) -> Rental:
        required = ["customer_id", "car_reg_num", "start_date", "end_date"]
        missing = [f for f in required if getattr(self, f) is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if not isinstance(self.start_date, date) or not isinstance(self.end_date, date):
            raise ValueError("start_date and end_date must be date objects")

        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

        if self.start_date < date.today():
            raise ValueError("start_date cannot be in the past")

        cars = db.load_vehicles(parameters = {"reg_num": self.car_reg_num})
        if not cars:
            raise ValueError(f"No vehicle found with reg_num '{self.car_reg_num}'")

        car = cars[0]
        if car["status"] != "active":
            raise ValueError(f"Vehicle '{self.car_reg_num}' is not active (status: {car['status']})")

        days = (self.end_date - self.start_date).days
        self.total_price = round(days * car["daily_rate"], 2)

        r = Rental(
            customer_id=self.customer_id,
            car_reg_num=self.car_reg_num,
            start_date=self.start_date,
            end_date=self.end_date,
            total_price=self.total_price,
            status=self.status or RentalStatus.pending,
        )

        save(r)
        return r