import requests
import os
from flask import Flask, request, jsonify, render_template, request, send_from_directory
from form import SignupForm, SigninForm
import random
import string
import re
import hashlib
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from geoalchemy2 import Geometry

app = Flask(__name__, static_url_path="", static_folder="static")

SECRET_KEY = os.urandom(32)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["RECAPTCHA_USE_SSL"] = True
app.config["RECAPTCHA_PUBLIC_KEY"] = os.getenv("RECAPTCHA_PUBLIC_KEY")
app.config["RECAPTCHA_PRIVATE_KEY"] = os.getenv("RECAPTCHA_PRIVATE_KEY")
app.config["RECAPTCHA_OPTIONS"] = {"theme": "black"}
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["MAIN_SITE_DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
db.app = app
db.init_app(app)
migrate = Migrate(app, db)

from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid



class Person(db.Model):
    __tablename__ = 'people'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    first_name = db.Column(db.String())
    middle_name = db.Column(db.String(), null=True)
    last_name = db.Column(db.String())
    birthdate = db.Column(db.DateTime())
    current_address_1 = db.Column(db.String(), null=True)
    current_address_2 = db.Column(db.String(), null=True)
    current_address_city = db.Column(db.String(), null=True)
    current_address_state = db.Column(db.String(), null=True)
    current_address_zip_code = db.Column(db.String(), null=True)
    current_gps_location = db.Column(Geometry('POINT'), null=True)
    social_security_number = db.Column(db.String(), null=True)
    drivers_license_or_state_id_state = db.Column(db.String(), null=True)
    drivers_license_or_state_id_number = db.Column(db.String(), null=True)
    height = db.Column(db.Float()) # in centimeters
    weight = db.Column(db.Interger())
    contacts = db.Column(JSON(), null=True) # keys: name, relationship_to_person, phone_numbers (keys: phone_number, type), address
    audit_trail = db.Column(JSON(), null=True) # log all access to the person's data (keys: email_address, ip, datetime, did_what, reason_for_access, agency, CAD_number, RMS_number)
    incidents = db.Column(JSON(), null=True)
    


if __name__ == "__main__":
    app.run(port=9000, debug=True)
