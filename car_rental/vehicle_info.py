from dataclasses import dataclass, asdict
from datetime import date
from enum import Enum
from typing import Optional
from .database import db_instance as db


class StrValueEnum(str, Enum):
    def __str__(self):
        return self.value

class VehicleType(StrValueEnum):
    car = 'car' # 4, 5 seats restriction
    van = 'van'
    suv = 'suv'
    mini = 'mini' # 2 seat restriction

class Location(StrValueEnum):
    madrid = 'madrid'
    barcelona = 'barcelona'
    valencia = 'valencia'
    sevilla ='sevilla'
    malaga = 'malaga'
    tenerife = 'tenerife'
    mallorca = 'mallorca'


class FuelType(StrValueEnum):
    petrol = 'petrol'
    diesel = 'diesel'
    electric = 'electric'
    hybrid = 'hybrid'


class TransmissionType(StrValueEnum):
    manual = 'manual'
    automatic = 'automatic'


class VehicleStatus(StrValueEnum):
    active = 'active'          # available
    maintenance = 'maintenance'  # temporarily unavailable
    retired = 'retired'        # removed

class RentalTier(StrValueEnum):
    economy = 'economy'
    midsize = 'midsize'
    luxury = 'luxury'


@dataclass
class Vehicle:
    type: VehicleType  # VehicleType.car
    brand: str  # Toyota
    model: str  # Corolla
    plate: str  # 3242 NRS
    location: Location # Location.madrid
    fuel: FuelType  # FuelType.hybrid
    transmission: TransmissionType  # TransmissionType.automatic
    seat_num: int  # 5
    manufacture_date: date  # 2022, 3, 1 - when the vehicle was built
    registration_date: date  # 2022, 6, 15 - when it joined the company, can't exceed 5 years after manufacture
    km: int  # 18500
    daily_rate: float  # 39.99
    status: VehicleStatus # VehicleStatus.active
    reg_num: str  # registration number 1HGM82633A004352
    category: RentalTier  # RentalTier.economy
    color: Optional[str] = None  # Silver

def save(vehicle: Vehicle):
    data = asdict(vehicle)
    for k, val in data.items():
        if hasattr(val, 'value'):
            data[k] = val.value
        elif isinstance(val, date):
            data[k] = val.isoformat()
    db.save_vehicle(data)

def update(reg_num: str, parameters: dict):
        if reg_num:
            db.update_vehicle(reg_num, parameters)
        else:
            raise ValueError("No reg_num provided")


class VehicleBuilder:
    def __init__(self):
        self.type = None
        self.brand = None
        self.model = None
        self.plate = None
        self.location = None
        self.fuel = None
        self.transmission = None
        self.seat_num = None
        self.manufacture_date = None
        self.registration_date = None
        self.km = None
        self.daily_rate = None
        self.status = None
        self.reg_num = None
        self.category = None
        self.color = None

    def with_type(self, type_: str):
        self.type = VehicleType(type_)
        return self

    def with_brand(self, brand: str):
        self.brand = brand
        return self

    def with_model(self, model: str):
        self.model = model
        return self

    def with_plate(self, plate: str):
        self.plate = plate
        return self

    def with_location(self, location: Location):
        self.location = location
        return self

    def with_fuel(self, fuel: str):
        self.fuel = FuelType(fuel)
        return self

    def with_transmission(self, transmission: str):
        self.transmission = TransmissionType(transmission)
        return self

    def with_seat_num(self, seat_num: int):
        self.seat_num = seat_num
        return self

    def with_manufacture_date(self, manufacture_date: date):
        self.manufacture_date = manufacture_date
        return self

    def with_registration_date(self, registration_date: date):
        self.registration_date = registration_date
        return self

    def with_km(self, km: int):
        self.km = km
        return self

    def with_daily_rate(self, daily_rate: float):
        self.daily_rate = daily_rate
        return self

    def with_status(self, status: str):
        self.status = VehicleStatus(status)
        return self

    def with_reg_num(self, reg_num: str):
        self.reg_num = reg_num
        return self

    def with_category(self, category: str):
        self.category = RentalTier(category)
        return self

    def with_color(self, color):
        self.color = color
        return self

    def build(self) -> Vehicle:
        required = ["type", "brand", "model", "plate", "location", "fuel",
                    "transmission", "seat_num", "manufacture_date",
                    "registration_date", "km", "daily_rate", "status",
                    "reg_num", "category"]
        missing = [f for f in required if getattr(self, f) is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if not isinstance(self.seat_num, int) or self.seat_num <= 0:
            raise ValueError(f"seat_num must be a positive integer, got '{self.seat_num}'")

        if self.type == VehicleType.mini and self.seat_num != 2:
            raise ValueError("Vehicles of type 'mini' must have exactly 2 seats")

        if self.type == VehicleType.car and self.seat_num not in (4, 5):
            raise ValueError("Vehicles of type 'car' must have 4 or 5 seats")

        if not isinstance(self.manufacture_date, date):
            raise ValueError(f"manufacture_date must be a date, got '{self.manufacture_date}'")

        if self.manufacture_date > date.today():
            raise ValueError("manufacture_date cannot be in the future")

        if not isinstance(self.registration_date, date):
            raise ValueError(f"registration_date must be a date, got '{self.registration_date}'")

        if self.registration_date < self.manufacture_date:
            raise ValueError("registration_date cannot be before manufacture_date")

        if (self.registration_date - self.manufacture_date).days > 5 * 365:
            raise ValueError("registration_date cannot exceed 5 years after manufacture_date")

        if not isinstance(self.km, int) or self.km < 0:
            raise ValueError(f"km must be a non-negative integer, got '{self.km}'")

        if not isinstance(self.daily_rate, (int, float)) or self.daily_rate <= 0:
            raise ValueError(f"daily_rate must be a positive number, got '{self.daily_rate}'")

        if not self.reg_num or not isinstance(self.reg_num, str):
            raise ValueError("reg_num must be a non-empty string")

        if not self.plate or not isinstance(self.plate, str):
            raise ValueError("plate must be a non-empty string")

        v = Vehicle(
            type=self.type,
            brand=self.brand,
            model=self.model,
            plate=self.plate,
            location=self.location,
            fuel=self.fuel,
            transmission=self.transmission,
            seat_num=self.seat_num,
            manufacture_date=self.manufacture_date,
            registration_date=self.registration_date,
            km=self.km,
            daily_rate=self.daily_rate,
            status=self.status,
            reg_num=self.reg_num,
            category=self.category,
            color=self.color,
        )

        save(v)
        return v