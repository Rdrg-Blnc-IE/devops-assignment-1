from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..database import db_instance as db
from ..vehicle_info import Location, VehicleType, FuelType, TransmissionType, RentalTier

customer_bp = Blueprint("customer", __name__, template_folder="../templates/customer")


@customer_bp.route("/", methods=["GET", "POST"])
@customer_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        raw_id = request.form.get("customer_id", "").strip()
        if raw_id:
            session["customer_id"] = raw_id
            return redirect(url_for("customer.dashboard"))
        flash("Please enter a valid Customer ID")

    return render_template("customer/login.html")


@customer_bp.route("/dashboard")
def dashboard():
    raw_customer_id = session.get("customer_id")
    if not raw_customer_id:
        return redirect(url_for("customer.login"))

    try:
        search_id = int(raw_customer_id)
    except (ValueError, TypeError):
        search_id = raw_customer_id

    rentals = db.load_reservations(parameters={"customer_id": search_id})

    return render_template(
        "customer/dashboard.html",
        customer_id=raw_customer_id,
        rentals=rentals
    )


@customer_bp.route("/browse-vehicles", methods=["GET"])
def browse_vehicles():
    """Tab 1: List all active vehicles with rich filters similar to Enterprise."""
    location = request.args.get("location", "")
    v_type = request.args.get("type", "")
    category = request.args.get("category", "")
    fuel = request.args.get("fuel", "")
    sort_by = request.args.get("sort_by", "")

    query_params = {"status": "active"}
    if location:
        query_params["location"] = location
    if v_type:
        query_params["type"] = v_type
    if category:
        query_params["category"] = category
    if fuel:
        query_params["fuel"] = fuel

    vehicles = db.load_vehicles(parameters=query_params)

    # Ordering options
    if sort_by == "price_asc":
        vehicles.sort(key=lambda x: x.get("daily_rate", 0))
    elif sort_by == "price_desc":
        vehicles.sort(key=lambda x: x.get("daily_rate", 0), reverse=True)

    return render_template(
        "customer/browse_vehicles.html",
        vehicles=vehicles,
        locations=[l.value for l in Location],
        types=[t.value for t in VehicleType],
        categories=[c.value for c in RentalTier],
        fuels=[f.value for f in FuelType],
        selected_location=location,
        selected_type=v_type,
        selected_category=category,
        selected_fuel=fuel,
        selected_sort=sort_by
    )


@customer_bp.route("/new-rental/<reg_num>", methods=["GET", "POST"])
def new_rental(reg_num):
    """Tab 2: Select dates and view full vehicle details anchored to vehicle location."""
    raw_customer_id = session.get("customer_id")
    if not raw_customer_id:
        return redirect(url_for("customer.login"))

    vehicles = db.load_vehicles(parameters={"reg_num": reg_num})
    vehicle = vehicles[0] if vehicles else None

    if not vehicle:
        return redirect(url_for("customer.browse_vehicles"))

    if request.method == "POST":
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        start_d = date.fromisoformat(start_date_str)
        end_d = date.fromisoformat(end_date_str)
        days = (end_d - start_d).days

        if days <= 0:
            flash("End date must be after start date")
            return render_template("customer/new_rental.html", vehicle=vehicle)

        total_price = round(days * vehicle["daily_rate"], 2)

        try:
            cust_id = int(raw_customer_id)
        except ValueError:
            cust_id = raw_customer_id

        db.save_reservation({
            "customer_id": cust_id,
            "car_reg_num": vehicle["reg_num"],
            "start_date": start_date_str,
            "end_date": end_date_str,
            "total_price": total_price,
            "status": "active"
        })
        return redirect(url_for("customer.dashboard"))

    return render_template("customer/new_rental.html", vehicle=vehicle)