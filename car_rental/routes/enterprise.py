from flask import Blueprint, render_template

enterprise_bp = Blueprint("enterprise", __name__, template_folder="../templates/enterprise")


@enterprise_bp.route("/")
def dashboard():
    return render_template("enterprise/dashboard.html", side="Enterprise")