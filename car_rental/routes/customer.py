from flask import Blueprint, render_template, request, redirect, url_for, session

customer_bp = Blueprint("customer", __name__, template_folder="../templates/customer")


# Route both "/" and "/login" to the same function
@customer_bp.route("/", methods=["GET", "POST"])
@customer_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")

        # Save customer_id to session
        session["customer_id"] = customer_id

        return redirect(url_for("customer.dashboard"))

    return render_template("customer/login.html", side="Customers")


@customer_bp.route("/dashboard")
def dashboard():
    customer_id = session.get("customer_id")
    if not customer_id:
        return redirect(url_for("customer.login"))

    return render_template("customer/dashboard.html", customer_id=customer_id)


@customer_bp.route("/new-rental", methods=["GET", "POST"])
def new_rental():
    if request.method == "POST":
        return redirect(url_for("customer.dashboard"))

    return render_template("customer/new_rental.html")


@customer_bp.route("/rental/<rental_id>", methods=["GET", "POST"])
def rental_detail(rental_id):
    if request.method == "POST":
        return redirect(url_for("customer.dashboard"))

    return render_template("customer/rental_detail.html", rental_id=rental_id)