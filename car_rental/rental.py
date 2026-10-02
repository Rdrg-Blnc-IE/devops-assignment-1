from dataclasses import dataclass
from datetime import date
from .database import DB
from .vehicle_info import StrValueEnum  # reuse the same base class


class RentalStatus(StrValueEnum):
    pending = 'pending'      # created, not yet confirmed
    confirmed = 'confirmed'  # confirmed, car not yet picked up
    active = 'active'        # car picked up, currently rented
    returned = 'returned'    # car returned, rental complete
    canceled = 'canceled'    # canceled before or during the rental


@dataclass
class Rental:
    id: int  # None until saved, assigned by DB, e.g. None, 7
    customer_id: int  # FK to a customer/user, e.g. 12
    car_reg_num: str  # FK to Vehicle.reg_num, e.g. "1HGCM82633A004352"
    start_date: date  # e.g. date(2026, 11, 1)
    end_date: date  # e.g. date(2026, 11, 5)
    total_price: float  # e.g. 199.95
    status: RentalStatus  # RentalStatus.pending

    def save(self, rental):
        DB.save_reservation(rental)

    def update(self, parameters):
        DB.update_reservation(self.id, parameters)


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
        # TODO: restriction of variables
        # - start_date/end_date must be date objects
        # - end_date must be after start_date
        # - start_date cannot be in the past
        # - look up car_reg_num's daily_rate from DB to compute total_price

        # TODO: send rental to database to save - DB.save_reservation()

        r = Rental(
            id=None,
            customer_id=self.customer_id,
            car_reg_num=self.car_reg_num,
            start_date=self.start_date,
            end_date=self.end_date,
            total_price=self.total_price,
            status=self.status,
        )

        Rental.save(r)
        return r