from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, List, Tuple

from .vehicle_info import Location, Vehicle


# Which locations are islands, and which single mainland city each one
# links to by ship.
island_locations = {Location.tenerife, Location.mallorca}
island_link = {
    Location.tenerife: Location.malaga,
    Location.mallorca: Location.valencia,
}


class Transport(ABC):
    def __init__(self, origin: Location, destination: Location):
        self.origin = origin
        self.destination = destination
        self.queue: deque = deque()

    @property
    @abstractmethod
    def mode(self) -> str:
        # 'truck' or 'ship'
        ...

    @property
    @abstractmethod
    def min_vehicles_to_depart(self) -> int:
        ...

    def enqueue(self, vehicle: Vehicle) -> None:
        if vehicle.location != self.origin:
            raise ValueError(
                f'Vehicle {vehicle.reg_num} is at {vehicle.location}, '
                f'not {self.origin} - cannot queue it for this trip'
            )
        self.queue.append(vehicle)

    def is_ready_to_depart(self) -> bool:
        return len(self.queue) >= self.min_vehicles_to_depart

    def depart(self) -> List[Vehicle]:
        if not self.is_ready_to_depart():
            raise ValueError(
                f'{self.mode} needs at least {self.min_vehicles_to_depart} '
                f'vehicles to depart ({len(self.queue)} queued)'
            )

        batch = [self.queue.popleft() for _ in range(self.min_vehicles_to_depart)]
        for vehicle in batch:
            vehicle.location = self.destination
            vehicle.update(vehicle.reg_num, {'location': self.destination.value})

        return batch



class Truck(Transport):
    @property
    def mode(self) -> str:
        return 'truck'

    @property
    def min_vehicles_to_depart(self) -> int:
        return 4


class Ship(Transport):
    @property
    def mode(self) -> str:
        return 'ship'

    @property
    def min_vehicles_to_depart(self) -> int:
        return 2


class TransportCreator(ABC):
    @abstractmethod
    def factory_method(self, origin: Location, destination: Location) -> Transport:
        ...

    def get_transport(self, origin: Location, destination: Location) -> Transport:
        return self.factory_method(origin, destination)


class TruckCreator(TransportCreator):
    def factory_method(self, origin: Location, destination: Location) -> Transport:
        return Truck(origin, destination)


class ShipCreator(TransportCreator):
    def factory_method(self, origin: Location, destination: Location) -> Transport:
        return Ship(origin, destination)


_truck_creator = TruckCreator()
_ship_creator = ShipCreator()



def resolve_route(origin: Location, destination: Location) -> List[Transport]:
    if origin == destination:
        raise ValueError('origin and destination must be different')

    origin_is_island = origin in island_locations
    dest_is_island = destination in island_locations

    # island -> island: ship to origin's link city, truck between the two
    # link cities (unless they're the same city), ship to the destination
    if origin_is_island and dest_is_island:
        origin_link = island_link[origin]
        dest_link = island_link[destination]
        trips = [_ship_creator.get_transport(origin, origin_link)]
        if origin_link != dest_link:
            trips.append(_truck_creator.get_transport(origin_link, dest_link))
        trips.append(_ship_creator.get_transport(dest_link, destination))
        return trips

    # mainland -> island
    if dest_is_island:
        link_city = island_link[destination]
        if origin == link_city:
            return [_ship_creator.get_transport(origin, destination)]
        return [
            _truck_creator.get_transport(origin, link_city),
            _ship_creator.get_transport(link_city, destination),
        ]

    # island -> mainland
    if origin_is_island:
        link_city = island_link[origin]
        if destination == link_city:
            return [_ship_creator.get_transport(origin, destination)]
        return [
            _ship_creator.get_transport(origin, link_city),
            _truck_creator.get_transport(link_city, destination),
        ]

    # mainland -> mainland
    return [_truck_creator.get_transport(origin, destination)]


class TransportQueueManager:
    def __init__(self):
        self._active: Dict[Tuple[Location, Location, str], Transport] = {}

    def request_transport(self, vehicle: Vehicle, final_destination: Location) -> None:
        trips = resolve_route(vehicle.location, final_destination)
        self._advance(vehicle, trips, trip_index=0)

    def _advance(self, vehicle: Vehicle, trips: List[Transport], trip_index: int) -> None:
        trip = trips[trip_index]
        key = (trip.origin, trip.destination, trip.mode)

        active_trip = self._active.setdefault(key, trip)
        active_trip.enqueue(vehicle)

        if active_trip.is_ready_to_depart():
            batch = active_trip.depart()
            del self._active[key]  # this trip's queue starts fresh next time

            if trip_index + 1 < len(trips):
                for moved_vehicle in batch:
                    self._advance(moved_vehicle, trips, trip_index + 1)

    def pending_trips(self) -> List[str]:
        return [
            f'{trip.mode}: {trip.origin} -> {trip.destination} '
            f'({len(trip.queue)}/{trip.min_vehicles_to_depart} queued)'
            for trip in self._active.values()
        ]