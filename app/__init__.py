from flask import Flask, render_template

# bagi kegunaan konfigurasi DB
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)
    # penetapan DB dan jenis engine DB yg  digunakan
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///meeting_room.db"
    
    # initialze Flask application
    db.init_app(app)
    migrate.init_app(app, db)
    # selesai initialze
    # import models ke Flask application
    from app import models

    # Flask route management
    @app.route("/")
    # default index route
    
    def index():
        # return "Sistem Tempahan Bilik Mesyuarat"
        # Lokasi file View 
        return render_template("index.html")

    return app