from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, Dict


class StrValueEnum(str, Enum):
    def __str__(self):
        return self.value

class VehicleType(StrValueEnum):
    car = 'car'
    truck = 'truck'
    motorbike = 'motorbike'
    van = 'van'
    suv = 'suv'
    mini = 'mini' # 2 seat number restriction


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
    plate: str  # NRS 3242
    fuel: FuelType  # FuelType.hybrid
    transmission: TransmissionType  # TransmissionType.automatic
    seat_num: int  # 5
    manufacture_date: date  # 2022, 3, 1 - when the vehicle was built
    registration_date: date  # 2022, 6, 15 - when it joined the company
    km: int  # 18500
    daily_rate: float  # 39.99
    status: VehicleStatus # VehicleStatus.active
    id_num: str  # 1HGCM82633A004352
    category: RentalTier  # RentalTier.economy
    features: Dict[str, str] = field(default_factory=list)  # ['GPS', 'Bluetooth', 'child seat']
    color: Optional[str] = None  # Silver


class VehicleBuilder:
    def __init__(self):
        self.type = None
        self.brand = None
        self.model = None
        self.plate = None
        self.fuel = None
        self.transmission = None
        self.seat_num = None
        self.manufacture_date = None
        self.registration_date = None
        self.km = None
        self.daily_rate = None
        self.status = None
        self.id_num = None
        self.category = None
        self.features = {}
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

    def with_id_num(self, id_num: str):
        self.id_num = id_num
        return self

    def with_category(self, category: str):
        self.category = RentalTier(category)
        return self

    def with_features(self, **kwargs):
        self.features = {
            **kwargs
        }
        return self

    def with_color(self, color):
        self.color = color
        return self

    def build(self) -> Vehicle:
        ...

        # TODO: restriction of variables ------------------------------

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
            self.id_num,
            self.category,
            self.features,
            self.color
        )