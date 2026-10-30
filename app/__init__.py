from flask import Flask, render_template

# load semua extension yg berkaitan
from app.extensions import (
    db,
    login_manager,
    mail,
    migrate,
    limiter,
)
from app.errors import register_error_handlers

# semua config file diletakkan dalam satu file
from config import Config

def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.from_object(Config)
        app.config.update(test_config)
    
    # initialze Flask application
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    # selesai initialze
    
    # setup database
    from app import models
    
    # Auth Blueprint
    from app.auth import auth_bp
    from app.auth import routes as auth_routes
    app.register_blueprint(auth_bp)
    
    # Admin Blueprint
    from app.admin import admin_bp
    from app.admin import routes as admin_routes
    app.register_blueprint(admin_bp)
    
    # Booking Blueprint
    from app.booking import booking_bp
    from app.booking import routes as booking_routes
    app.register_blueprint(booking_bp)
    
    # setup utk akaun admin, selepas model di import
    from app.admin_setup import ensure_default_admin

    if not app.config.get("TESTING"):
        with app.app_context():
            ensure_default_admin(app)
        
    # Flask route management
    @app.route("/")
    # default index route
    
    def index():
        # return "Sistem Tempahan Bilik Mesyuarat"
        # Lokasi file View 
        return render_template("index.html")

    # ========================
    # Security Headers
    # ========================
    @app.after_request
    def add_security_headers(response):
        response.headers[
            "X-Content-Type-Options"
        ] = "nosniff"

        response.headers[
            "X-Frame-Options"
        ] = "SAMEORIGIN"

        response.headers[
            "Referrer-Policy"
        ] = "strict-origin-when-cross-origin"

        response.headers[
            "Permissions-Policy"
        ] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        )

        return response
    
    # ========================
    # Error Handlers
    # ========================
    register_error_handlers(app)
    
    return app