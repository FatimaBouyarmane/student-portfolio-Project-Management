import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "dev_secret_key_123")  # Default secret key for development
app.secret_key = app.config["SECRET_KEY"]
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# mail configuration
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@studentportfolio.com")

# Check if email is configured
MAIL_ENABLED = app.config["MAIL_USERNAME"] is not None and app.config["MAIL_PASSWORD"] is not None

# initialize extensions
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# token serializer for email confirmation
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# import routes
from routes import *  # noqa: F401, E402

with app.app_context():
    # Import the models here
    import models  # noqa: F401

    # Create all tables
    db.create_all()