from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for
from ..database import db_instance as db
from ..vehicle_info import Location, VehicleType, FuelType, TransmissionType, RentalTier, VehicleStatus
from ..transport import TransportQueueManager

enterprise_bp = Blueprint("enterprise", __name__, template_folder="../templates/enterprise")
transport_manager = TransportQueueManager()


@enterprise_bp.route("/")
@enterprise_bp.route("/dashboard")
def dashboard():
    vehicles = db.load_vehicles()
    rentals = db.load_reservations()
    customers = db.load_customers()

    active_rentals = [r for r in rentals if r.get("status") == "active"]
    available_vehicles = [v for v in vehicles if v.get("status") == "active"]

    return render_template(
        "enterprise/dashboard.html",
        total_vehicles=len(vehicles),
        available_vehicles=len(available_vehicles),
        active_rentals=len(active_rentals),
        total_customers=len(customers),
        pending_trips_count=len(transport_manager.pending_trips())
    )


@enterprise_bp.route("/vehicles", methods=["GET"])
def vehicle_list():
    status = request.args.get("status", "")
    location = request.args.get("location", "")
    v_type = request.args.get("type", "")
    category = request.args.get("category", "")
    fuel = request.args.get("fuel", "")
    color = request.args.get("color", "")
    sort_by = request.args.get("sort_by", "")

    query_params = {}
    if status:
        query_params["status"] = status
    if location:
        query_params["location"] = location
    if v_type:
        query_params["type"] = v_type
    if category:
        query_params["category"] = category
    if fuel:
        query_params["fuel"] = fuel
    if color:
        query_params["color"] = color

    vehicles = db.load_vehicles(parameters=query_params if query_params else None)

    # Sorting options
    if sort_by == "price_asc":
        vehicles.sort(key=lambda x: x.get("daily_rate", 0))
    elif sort_by == "price_desc":
        vehicles.sort(key=lambda x: x.get("daily_rate", 0), reverse=True)
    elif sort_by == "km_asc":
        vehicles.sort(key=lambda x: x.get("km", 0))
    elif sort_by == "km_desc":
        vehicles.sort(key=lambda x: x.get("km", 0), reverse=True)

    return render_template(
        "enterprise/vehicle_list.html",
        vehicles=vehicles,
        locations=[l.value for l in Location],
        types=[t.value for t in VehicleType],
        statuses=[s.value for s in VehicleStatus],
        categories=[c.value for c in RentalTier],
        fuels=[f.value for f in FuelType],
        selected_status=status,
        selected_location=location,
        selected_type=v_type,
        selected_category=category,
        selected_fuel=fuel,
        selected_color=color,
        selected_sort=sort_by
    )


@enterprise_bp.route("/vehicles/new", methods=["GET", "POST"])
def vehicle_new():
    color_options = ["Black", "White", "Silver", "Grey", "Blue", "Red", "Green"]

    if request.method == "POST":
        vehicle_data = {
            "reg_num": request.form.get("reg_num"),
            "brand": request.form.get("brand"),
            "model": request.form.get("model"),
            "type": request.form.get("type"),
            "category": request.form.get("category"),
            "daily_rate": float(request.form.get("daily_rate", 0)),
            "seat_num": int(request.form.get("seat_num", 5)),
            "plate": request.form.get("plate"),
            "color": request.form.get("color"),
            "fuel": request.form.get("fuel"),
            "transmission": request.form.get("transmission"),
            "km": int(request.form.get("km", 0)),
            "status": request.form.get("status", "active"),
            "location": request.form.get("location"),
            "manufacture_date": request.form.get("manufacture_date"),
            "registration_date": date.today().isoformat()  # Auto use today's date
        }
        db.save_vehicle(vehicle_data)
        return redirect(url_for("enterprise.vehicle_list"))

    return render_template(
        "enterprise/vehicle_new.html",
        locations=[l.value for l in Location],
        types=[t.value for t in VehicleType],
        fuels=[f.value for f in FuelType],
        transmissions=[tr.value for tr in TransmissionType],
        tiers=[tier.value for tier in RentalTier],
        statuses=[s.value for s in VehicleStatus],
        colors=color_options
    )


@enterprise_bp.route("/vehicles/<reg_num>", methods=["GET", "POST"])
def vehicle_detail(reg_num):
    vehicles = db.load_vehicles(parameters={"reg_num": reg_num})
    vehicle = vehicles[0] if vehicles else None

    if request.method == "POST":
        # Allow changing ONLY category, daily_rate, and status
        updates = {
            "category": request.form.get("category"),
            "daily_rate": float(request.form.get("daily_rate")),
            "status": request.form.get("status")
        }
        db.update_vehicle(reg_num, updates)
        return redirect(url_for("enterprise.vehicle_list"))

    return render_template(
        "enterprise/vehicle_detail.html",
        vehicle=vehicle,
        categories=[c.value for c in RentalTier],
        statuses=[s.value for s in VehicleStatus]
    )


@enterprise_bp.route("/transport/new", methods=["GET", "POST"])
def transport_new():
    if request.method == "POST":
        reg_num = request.form.get("reg_num")
        dest_str = request.form.get("destination")

        vehicles = db.load_vehicles(parameters={"reg_num": reg_num})
        if vehicles:
            v_dict = vehicles[0]
            from car_rental.vehicle_info import Vehicle
            v_obj = Vehicle(
                type=VehicleType(v_dict["type"]),
                brand=v_dict["brand"],
                model=v_dict["model"],
                plate=v_dict["plate"],
                location=Location(v_dict["location"]),
                fuel=FuelType(v_dict["fuel"]),
                transmission=TransmissionType(v_dict["transmission"]),
                seat_num=v_dict["seat_num"],
                manufacture_date=v_dict["manufacture_date"],
                registration_date=v_dict["registration_date"],
                km=v_dict["km"],
                daily_rate=v_dict["daily_rate"],
                status=VehicleStatus(v_dict["status"]),
                reg_num=v_dict["reg_num"],
                category=RentalTier(v_dict["category"])
            )
            transport_manager.request_transport(v_obj, Location(dest_str))

        return redirect(url_for("enterprise.transport_queue"))

    vehicles = db.load_vehicles(parameters={"status": "active"})
    return render_template(
        "enterprise/transport_new.html",
        vehicles=vehicles,
        locations=[l.value for l in Location]
    )


@enterprise_bp.route("/transport/queue")
def transport_queue():
    trips = transport_manager.pending_trips()
    return render_template("enterprise/transport_queue.html", pending_trips=trips)


@enterprise_bp.route("/rentals", methods=["GET"])
def rental_list():
    status = request.args.get("status", "")
    customer_id = request.args.get("customer_id", "")

    query_params = {}
    if status:
        query_params["status"] = status
    if customer_id:
        try:
            query_params["customer_id"] = int(customer_id)
        except ValueError:
            query_params["customer_id"] = customer_id

    rentals = db.load_reservations(parameters=query_params if query_params else None)

    return render_template(
        "enterprise/rental_list.html",
        rentals=rentals,
        selected_status=status,
        selected_customer_id=customer_id
    )


@enterprise_bp.route("/rentals/<int:rental_id>", methods=["GET", "POST"])
def rental_detail(rental_id):
    rentals = db.load_reservations(parameters={"id": rental_id})
    rental = rentals[0] if rentals else None

    if request.method == "POST":
        updates = {
            "status": request.form.get("status"),
            "end_date": request.form.get("end_date"),
            "total_price": float(request.form.get("total_price"))
        }
        db.update_reservation(rental_id, updates)
        return redirect(url_for("enterprise.rental_list"))

    return render_template("enterprise/rental_detail.html", rental=rental)


@enterprise_bp.route("/customers", methods=["GET"])
def customer_list():
    location = request.args.get("location", "")
    search = request.args.get("search", "")

    query_params = {}
    if location:
        query_params["location"] = location

    customers = db.load_customers(parameters=query_params if query_params else None)

    if search:
        search_lower = search.lower()
        customers = [
            c for c in customers
            if search_lower in c.get("name", "").lower()
               or search_lower in c.get("surname", "").lower()
               or search_lower in c.get("email", "").lower()
        ]

    return render_template(
        "enterprise/customer_list.html",
        customers=customers,
        locations=[l.value for l in Location],
        selected_location=location,
        search_query=search
    )