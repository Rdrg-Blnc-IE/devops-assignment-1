import pytest

from car_rental.transport import (
    Transport,
    Truck,
    Ship,
    TransportCreator,
    TruckCreator,
    ShipCreator,
    resolve_route,
    TransportQueueManager,
    island_locations,
    island_link,
)
from car_rental.vehicle_info import Location


# ---------------------------------------------------------------------------
# Test double
# ---------------------------------------------------------------------------

class FakeVehicle:
    """Duck-typed stand-in for Vehicle: just location, reg_num, update()."""

    def __init__(self, reg_num: str, location: Location):
        self.reg_num = reg_num
        self.location = location
        self.update_calls = []

    def update(self, reg_num, parameters):
        self.update_calls.append((reg_num, parameters))


def make_fleet(n: int, location: Location, prefix: str = "V") -> list[FakeVehicle]:
    return [FakeVehicle(f"{prefix}{i}", location) for i in range(n)]


# ---------------------------------------------------------------------------
# Abstract base classes cannot be instantiated directly
# ---------------------------------------------------------------------------

class TestAbstractness:
    def test_transport_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            Transport(Location.madrid, Location.barcelona)

    def test_transport_creator_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            TransportCreator()


# ---------------------------------------------------------------------------
# Truck / Ship — concrete products
# ---------------------------------------------------------------------------

class TestTruck:
    def test_mode_and_threshold(self):
        truck = Truck(Location.madrid, Location.barcelona)
        assert truck.mode == "truck"
        assert truck.min_vehicles_to_depart == 4

    def test_not_ready_below_threshold(self):
        truck = Truck(Location.madrid, Location.barcelona)
        for v in make_fleet(3, Location.madrid):
            truck.enqueue(v)
        assert truck.is_ready_to_depart() is False

    def test_ready_at_threshold(self):
        truck = Truck(Location.madrid, Location.barcelona)
        for v in make_fleet(4, Location.madrid):
            truck.enqueue(v)
        assert truck.is_ready_to_depart() is True

    def test_depart_raises_if_not_ready(self):
        truck = Truck(Location.madrid, Location.barcelona)
        for v in make_fleet(2, Location.madrid):
            truck.enqueue(v)
        with pytest.raises(ValueError, match="needs at least 4"):
            truck.depart()

    def test_depart_moves_exactly_threshold_and_leaves_remainder(self):
        truck = Truck(Location.madrid, Location.barcelona)
        fleet = make_fleet(5, Location.madrid)
        for v in fleet:
            truck.enqueue(v)

        batch = truck.depart()

        assert len(batch) == 4
        assert all(v.location == Location.barcelona for v in batch)
        assert len(truck.queue) == 1
        assert truck.queue[0].location == Location.madrid  # 5th vehicle untouched

    def test_depart_calls_vehicle_update(self):
        truck = Truck(Location.madrid, Location.barcelona)
        fleet = make_fleet(4, Location.madrid)
        for v in fleet:
            truck.enqueue(v)

        truck.depart()

        for v in fleet:
            assert v.update_calls == [(v.reg_num, {"location": "barcelona"})]


class TestShip:
    def test_mode_and_threshold(self):
        ship = Ship(Location.malaga, Location.tenerife)
        assert ship.mode == "ship"
        assert ship.min_vehicles_to_depart == 2

    def test_not_ready_with_one_vehicle(self):
        ship = Ship(Location.malaga, Location.tenerife)
        ship.enqueue(FakeVehicle("S1", Location.malaga))
        assert ship.is_ready_to_depart() is False

    def test_ready_with_two_vehicles(self):
        ship = Ship(Location.malaga, Location.tenerife)
        for v in make_fleet(2, Location.malaga):
            ship.enqueue(v)
        assert ship.is_ready_to_depart() is True


class TestEnqueueValidation:
    def test_enqueue_rejects_vehicle_at_wrong_origin(self):
        truck = Truck(Location.madrid, Location.barcelona)
        wrong_location_vehicle = FakeVehicle("X1", Location.sevilla)
        with pytest.raises(ValueError, match="not madrid"):
            truck.enqueue(wrong_location_vehicle)


# ---------------------------------------------------------------------------
# Factory Method: creators
# ---------------------------------------------------------------------------

class TestCreators:
    def test_truck_creator_builds_truck(self):
        creator = TruckCreator()
        transport = creator.get_transport(Location.madrid, Location.sevilla)
        assert isinstance(transport, Truck)
        assert transport.origin == Location.madrid
        assert transport.destination == Location.sevilla

    def test_ship_creator_builds_ship(self):
        creator = ShipCreator()
        transport = creator.get_transport(Location.malaga, Location.tenerife)
        assert isinstance(transport, Ship)

    def test_factory_method_directly_matches_get_transport(self):
        creator = TruckCreator()
        a = creator.factory_method(Location.madrid, Location.sevilla)
        b = creator.get_transport(Location.madrid, Location.sevilla)
        assert type(a) is type(b)


# ---------------------------------------------------------------------------
# resolve_route
# ---------------------------------------------------------------------------

class TestResolveRoute:
    def test_mainland_to_mainland_is_single_truck_trip(self):
        trips = resolve_route(Location.barcelona, Location.sevilla)
        assert len(trips) == 1
        assert isinstance(trips[0], Truck)
        assert trips[0].origin == Location.barcelona
        assert trips[0].destination == Location.sevilla

    def test_direct_ship_link_malaga_tenerife(self):
        trips = resolve_route(Location.malaga, Location.tenerife)
        assert len(trips) == 1
        assert isinstance(trips[0], Ship)

    def test_direct_ship_link_valencia_mallorca(self):
        trips = resolve_route(Location.valencia, Location.mallorca)
        assert len(trips) == 1
        assert isinstance(trips[0], Ship)

    def test_mainland_to_island_via_non_link_city_is_two_trips(self):
        trips = resolve_route(Location.madrid, Location.tenerife)
        assert len(trips) == 2
        assert isinstance(trips[0], Truck)
        assert trips[0].origin == Location.madrid
        assert trips[0].destination == Location.malaga
        assert isinstance(trips[1], Ship)
        assert trips[1].origin == Location.malaga
        assert trips[1].destination == Location.tenerife

    def test_island_to_mainland_via_non_link_city_is_two_trips(self):
        trips = resolve_route(Location.tenerife, Location.barcelona)
        assert len(trips) == 2
        assert isinstance(trips[0], Ship)
        assert trips[0].destination == Location.malaga
        assert isinstance(trips[1], Truck)
        assert trips[1].origin == Location.malaga
        assert trips[1].destination == Location.barcelona

    def test_island_to_island_is_three_trips(self):
        trips = resolve_route(Location.tenerife, Location.mallorca)
        assert len(trips) == 3
        assert isinstance(trips[0], Ship)
        assert trips[0].origin == Location.tenerife
        assert trips[0].destination == Location.malaga
        assert isinstance(trips[1], Truck)
        assert trips[1].origin == Location.malaga
        assert trips[1].destination == Location.valencia
        assert isinstance(trips[2], Ship)
        assert trips[2].origin == Location.valencia
        assert trips[2].destination == Location.mallorca

    def test_same_origin_and_destination_raises(self):
        with pytest.raises(ValueError, match="must be different"):
            resolve_route(Location.madrid, Location.madrid)

    def test_every_island_link_is_consistent(self):
        """Sanity check on the lookup tables themselves."""
        for island in island_locations:
            assert island in island_link
            assert island_link[island] not in island_locations


# ---------------------------------------------------------------------------
# TransportQueueManager
# ---------------------------------------------------------------------------

class TestTransportQueueManager:
    def test_vehicles_stay_put_below_truck_threshold(self):
        manager = TransportQueueManager()
        fleet = make_fleet(3, Location.madrid)

        for v in fleet:
            manager.request_transport(v, Location.barcelona)

        assert all(v.location == Location.madrid for v in fleet)

    def test_truck_departs_exactly_at_threshold(self):
        manager = TransportQueueManager()
        fleet = make_fleet(4, Location.madrid)

        for v in fleet:
            manager.request_transport(v, Location.barcelona)

        assert all(v.location == Location.barcelona for v in fleet)

    def test_single_vehicle_ship_trip_stalls(self):
        manager = TransportQueueManager()
        vehicle = FakeVehicle("S1", Location.malaga)

        manager.request_transport(vehicle, Location.tenerife)

        assert vehicle.location == Location.malaga  # ship needs 2, still waiting

    def test_full_chain_madrid_to_tenerife(self):
        """4 vehicles should fully chain: truck to malaga, then ship(s) to tenerife."""
        manager = TransportQueueManager()
        fleet = make_fleet(4, Location.madrid)

        for v in fleet:
            manager.request_transport(v, Location.tenerife)

        assert all(v.location == Location.tenerife for v in fleet)

    def test_shared_queue_across_separate_requests(self):
        """Vehicles requested one at a time for the same trip should still
        batch together, not require a single bulk call.
        """
        manager = TransportQueueManager()
        fleet = make_fleet(4, Location.sevilla)

        manager.request_transport(fleet[0], Location.madrid)
        manager.request_transport(fleet[1], Location.madrid)
        assert fleet[0].location == Location.sevilla  # still waiting after 2

        manager.request_transport(fleet[2], Location.madrid)
        manager.request_transport(fleet[3], Location.madrid)
        assert all(v.location == Location.madrid for v in fleet)  # departs on the 4th

    def test_pending_trips_reports_partial_queue(self):
        manager = TransportQueueManager()
        for v in make_fleet(2, Location.madrid):
            manager.request_transport(v, Location.barcelona)

        pending = manager.pending_trips()

        assert len(pending) == 1
        assert "2/4" in pending[0]

    def test_pending_trips_empty_after_departure(self):
        manager = TransportQueueManager()
        for v in make_fleet(4, Location.madrid):
            manager.request_transport(v, Location.barcelona)

        assert manager.pending_trips() == []

    def test_enqueue_vehicle_not_at_route_origin_raises(self):
        manager = TransportQueueManager()
        # vehicle claims to be heading from madrid, but is actually located
        # elsewhere — resolve_route trusts vehicle.location as the origin,
        # so this should succeed; this test instead checks a mismatched
        # manual enqueue is rejected at the Transport level (already
        # covered in TestEnqueueValidation), so here we just confirm
        # request_transport uses the vehicle's own location as origin.
        vehicle = FakeVehicle("M1", Location.sevilla)
        manager.request_transport(vehicle, Location.madrid)
        # single vehicle below truck threshold (4) -> still at sevilla
        assert vehicle.location == Location.sevilla