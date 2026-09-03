from flask import Flask, render_template

# bagi kegunaan konfigurasi DB
from app.extensions import db, migrate

# semua config file diletakkan dalam satu file
from config import Config

# setup utk akaun admin
from app.admin_setup import ensure_default_admin

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)
    
    # initialze Flask application
    db.init_app(app)
    migrate.init_app(app, db)
    # selesai initialze
    # DB setup
    from app import models

    from app.auth import auth_bp
    from app.auth import routes

    app.register_blueprint(auth_bp)
    
    # setup utk akaun admin, selepas model di import
    from app.admin_setup import ensure_default_admin
    with app.app_context():
        ensure_default_admin(app)
        
    # Flask route management
    @app.route("/")
    # default index route
    
    def index():
        # return "Sistem Tempahan Bilik Mesyuarat"
        # Lokasi file View 
        return render_template("index.html")

    return app