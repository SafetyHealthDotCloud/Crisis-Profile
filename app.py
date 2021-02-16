import requests
import os
from flask import Flask, request, jsonify, render_template, request, send_from_directory
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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DEV_DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
db.app = app
db.init_app(app)
migrate = Migrate(app, db)

from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    email_address = db.Column(db.String(), unique=True)
    emailed_verification_code = db.Column(db.String(), nullable=True)
    datetime_verification_code_created = db.Column(db.DateTime, nullable = False)
    is_professional = db.Column(db.Boolean(), default=False)
    person_id = db.Column(db.String(), db.ForeignKey('people.id'), nullable=True)

class Person(db.Model):
    __tablename__ = 'people'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    first_name = db.Column(db.String())
    middle_name = db.Column(db.String(), nullable=True)
    last_name = db.Column(db.String())
    aliases = db.Column(JSON(), nullable=True)
    photographs = db.Column(JSON(), nullable=True)
    date_of_birth = db.Column(db.DateTime())
    persons_phone_numbers = db.Column(JSON(), nullable=True)
    current_physical_living_address_1 = db.Column(db.String(), nullable=True)
    current_physical_living_address_2 = db.Column(db.String(), nullable=True)
    current_physical_living_address_city = db.Column(db.String(), nullable=True)
    current_physical_living_address_state = db.Column(db.String(), nullable=True)
    current_physical_living_address_zip_code = db.Column(db.String(), nullable=True)
    past_physical_living_addresses = db.Column(JSON(), nullable=True)
    locations_frequent = db.Column(JSON(), nullable=True)
    current_gps_location = db.Column(Geometry('POINT'), nullable=True)
    vehicles = db.Column(JSON(), nullable=True)
    social_security_number_salt = db.Column(db.String(), nullable=True)
    social_security_number_hash = db.Column(db.String(), nullable=True)
    drivers_license_or_state_id_state = db.Column(db.String(), nullable=True)
    drivers_license_or_state_id_number = db.Column(db.String(), nullable=True)
    height = db.Column(db.Float(), nullable=True) # in centimeters
    weight = db.Column(db.Integer(), nullable=True)
    eye_color = db.Column(db.String(), nullable=True)
    hair_color = db.Column(db.String(), nullable=True)
    race = db.Column(db.String(), nullable=True)
    tattoos = db.Column(JSON(), nullable=True)
    scars = db.Column(db.String(), nullable=True)
    marks = db.Column(db.String(), nullable=True)
    contacts = db.Column(JSON(), nullable=True) # keys: name, relationship_to_person, phone_numbers (keys: phone_number, type), address
    audit_trail = db.Column(JSON(), nullable=True) # log all access to the person's data (keys: email_address, ip, datetime, did_what, reason_for_access, agency, CAD_number, RMS_number)
    incidents = db.Column(JSON(), nullable=True)
    allergies = db.Column(JSON(), nullable=True)
    medical_conditions = db.Column(JSON(), nullable=True)
    mental_health_conditions = db.Column(JSON(), nullable=True)
    languages = db.Column(JSON(), nullable=True)
    medications = db.Column(JSON(), nullable=True)
    appointments = db.Column(JSON(), nullable=True)
    safety_information = db.Column(db.String(), nullable=True)
    deescalation_instructions = db.Column(db.String(), nullable=True)
    documents = db.Column(JSON(), nullable=True)

@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)

@app.route("/for_first_responders", methods=["GET"])
def first_responder_home():
    return render_template(
        "for_first_responders.html",
        polly_api_key=os.getenv('POLLY_API_KEY'),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY')
    )



def create_random_string():
    letters = string.ascii_lowercase
    return "".join([random.choice(letters) for i in range(10)])

@app.route("/send_login_email", methods=["POST"])
def send_login_email():
    verification_token = create_random_string()
    print('email ', request.form)
    email = requests.post(
        "https://api.mailgun.net/v3/%s/messages" % (os.getenv("API_EMAIL_DOMAIN_NAME")),
        auth=("api", "%s" % (os.getenv("MAILGUN_API_KEY"))),
        data={
            "from": "Emergency.help <no-reply@%s>"
            % (os.getenv("API_EMAIL_DOMAIN_NAME")),
            "to": ["%s" % (request.form.get('email'))],
            "subject": "Login code for Emergency.help",
            "text": 'Hi! This is a login email for Emergency.help. Enter the code: %s on Emergency.help'
            % (
                verification_token,
            ),
        },
    ).text
    print('email status', email)
    return jsonify("email sent")

@app.route("/", methods=["GET"])
def home():
    return render_template(
        "index.html",
        polly_api_key=os.getenv('POLLY_API_KEY'),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY')
    )


if __name__ == "__main__":
    app.run(port=9000, debug=True)
