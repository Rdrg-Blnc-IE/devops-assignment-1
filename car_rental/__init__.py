from flask import Flask, render_template
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from .routes.customer import customer_bp
    from .routes.enterprise import enterprise_bp
    app.register_blueprint(customer_bp, url_prefix="/customer")
    app.register_blueprint(enterprise_bp, url_prefix="/enterprise")

    @app.route("/")
    def index():
        return render_template("index.html")

    return app