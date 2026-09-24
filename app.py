from car_rental.vehicle_info import VehicleBuilder

car1 = (
        VehicleBuilder()
        .with_fuel('petrol')
        .with_type('car')
        )

print(car1.fuel)
print(car1.type)