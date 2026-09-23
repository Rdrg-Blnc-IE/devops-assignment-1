from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class VehicleType(str, Enum):
    car = 'car'
    truck = 'truck'
    motorbike = 'motorbike'
    van = 'van'
    suv = 'suv'
    mini = 'mini' # 2 seat number restriction


class FuelType(str, Enum):
    petrol = 'petrol'
    diesel = 'diesel'
    electric = 'electric'
    hybrid = 'hybrid'


class TransmissionType(str, Enum):
    manual = 'manual'
    automatic = 'automatic'


class VehicleStatus(str, Enum):
    active = 'active'          # available
    maintenance = 'maintenance'  # temporarily unavailable
    retired = 'retired'        # removed

class RentalTier(str, Enum):
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
    features: list[str] = field(default_factory=list)  # ['GPS', 'Bluetooth', 'child seat']
    color: Optional[str] = None  # Silver