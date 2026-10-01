from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional
from .database import DB


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
    mallorca = 'mallorrca'


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
        ...

        # TODO: restriction of variables

        # TODO: send vehicle to database to save - DB.save()

        return Vehicle(
            self.type,
            self.brand,
            self.model,
            self.plate,
            self.fuel,
            self.transmission,
            self.seat_num,
            self.manufacture_date,
            self.registration_date,
            self.km,
            self.daily_rate,
            self.status,
            self.reg_num,
            self.category,
            self.color
        )