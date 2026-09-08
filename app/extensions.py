from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_mail import Mail


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

login_manager.login_view = "auth.login"
login_manager.login_message = "Sila log masuk untuk mengakses halaman ini."
login_manager.login_message_category = "warning"