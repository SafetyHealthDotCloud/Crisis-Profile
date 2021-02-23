import requests
import os
from flask import Flask, session, request, jsonify, render_template, request, send_from_directory
import random
import string
import re
import hashlib
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from geoalchemy2 import Geometry
import sqlalchemy
import datetime
import json

app = Flask(__name__, static_url_path="", static_folder="static")

SECRET_KEY = os.urandom(32)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DEV_DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
db.app = app
db.init_app(app)
migrate = Migrate(app, db)

from flask_login import LoginManager
from flask_login import login_user
from flask_login import current_user
from flask_login import UserMixin
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

def create_random_string():
    letters = string.ascii_lowercase
    return "".join([random.choice(letters) for i in range(10)])

@app.before_request
def make_session_permanent():
    session.permanent = True

# When someone puts in their email address
# we compare it to list of approved work email
# addresses and domains
class ApprovedWorkEmailAddressDomain(db.Model):
    __tablename__ = 'approved_work_email_address_domains'

    email_address_domain = db.Column(db.String(), primary_key=True)

    def __init__(self, email_address_domain):
        self.email_address_domain = email_address_domain

class ApprovedWorkEmailAddress(db.Model):
    __tablename__ = 'approved_work_email_addresses'

    email_address = db.Column(db.String(), primary_key=True)

    def __init__(self, email_address_domain):
        self.email_address = email_address

from datetime import date, timedelta
  
def calculate_age(birth_date): 
    return (date.today() - birth_date) // timedelta(days=365.2425)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    email_address = db.Column(db.String(), unique=True)
    emailed_verification_code = db.Column(db.String(), nullable=True)
    datetime_verification_code_created = db.Column(db.DateTime, server_default=sqlalchemy.sql.func.now())
    is_professional = db.Column(db.Boolean(), default=False)
    person_id = db.Column(UUID(as_uuid=True), db.ForeignKey('people.id'), nullable=True)
    job_title = db.Column(db.String(), nullable=True)
    organization = db.Column(db.String(), nullable=True)
    
    def __init__(self, email_address, emailed_verification_code, is_professional, person_id, job_title, agency):
        self.email_address = email_address
        self.emailed_verification_code = emailed_verification_code
        self.is_professional = is_professional
        self.person_id = person_id
        self.job_title = job_title
        self.agency = agency

    def to_json(self):      
        print(Person.query.filter_by(id=self.person_id).first() ) 
        person_query = Person.query.filter_by(id=self.person_id)
        data = {"email_address": self.email_address}
        if person_query.scalar():
            person = person_query.first()
            data['first_name'] = person.first_name
            data['middle_name'] = person.middle_name
            data['last_name'] = person.last_name
            data['preferred_name'] = person.preferred_name
            data['preferred_gender_pronouns'] = person.preferred_gender_pronouns
            data['date_of_birth'] = person.date_of_birth.strftime("%B %-d, %Y")
            data['age'] = calculate_age(person.date_of_birth.date())
            data['contacts'] = person.contacts
            data['persons_phone_numbers'] = person.persons_phone_numbers
            data['current_physical_living_address_1'] = person.current_physical_living_address_1
            data['current_physical_living_address_2'] = person.current_physical_living_address_2
            data['current_physical_living_address_city'] = person.current_physical_living_address_city
            data['current_physical_living_address_state'] = person.current_physical_living_address_state
            data['current_physical_living_address_zip_code'] = person.current_physical_living_address_zip_code
        
        return data

    def is_authenticated(self):
        return True

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False          

    def get_id(self):         
        return str(self.id)    


class Person(db.Model):
    __tablename__ = 'people'

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sqlalchemy.text("uuid_generate_v4()"), unique=True)
    first_name = db.Column(db.String())
    middle_name = db.Column(db.String(), nullable=True)
    last_name = db.Column(db.String())
    preferred_name = db.Column(db.String(), nullable=True)
    preferred_gender_pronouns = db.Column(db.String(), nullable=True)
    aliases = db.Column(JSON(), nullable=True)
    photographs = db.Column(JSON(), nullable=True)
    date_of_birth = db.Column(db.Date())
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
    mental_health_triggers = db.Column(JSON(), nullable=True)
    mental_health_baseline_behavior = db.Column(JSON(), nullable=True)
    no_contact_orders = db.Column(JSON(), nullable=True)

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




@app.route("/send_login_email", methods=["POST"])
def send_login_email():
    email_address = request.form['email']
    verification_token = create_random_string()
    does_email_exist = db.session.query(User.id).filter_by(email_address=request.form['email']).scalar() is not None
    if does_email_exist:
        user = User.query.filter_by(email_address=email_address).first()
        user.emailed_verification_code = verification_token
        user.datetime_verification_code_created = datetime.datetime.utcnow()
        db.session.commit()
    else:
        user = User(email_address, verification_token, None, None, None, None)
        db.session.add(user)
        db.session.commit()
    if os.environ.get('IS_DEV_AUTO_LOGIN', False) == 'true':
        return jsonify("email sent")
    email = requests.post(
        "https://api.mailgun.net/v3/%s/messages" % (os.getenv("API_EMAIL_DOMAIN_NAME")),
        auth=("api", "%s" % (os.getenv("MAILGUN_API_KEY"))),
        data={
            "from": "SafetyHealth.cloud <no-reply@%s>"
            % (os.getenv("API_EMAIL_DOMAIN_NAME")),
            "to": ["%s" % (request.form.get('email'))],
            "subject": "Login code for SafetyHealth.cloud",
            "text": 'Hi! This is a login email for SafetyHealth.cloud. Enter the code: %s on SafetyHealth.cloud'
            % (
                verification_token,
            ),
        },
    ).text
    return jsonify("email sent")

@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()

@app.route('/login', methods=['POST'])
def login():
    if os.environ.get('IS_DEV_AUTO_LOGIN', False) == 'true':
        email_address = os.environ.get("AUTO_LOGIN_EMAIL", "")
        user_query = User.query.filter_by(email_address=email_address)
    else:
        info = request.form
        email_address = info['email_address']
        code = info['code'].strip()
        user_query = User.query.filter_by(email_address=email_address, emailed_verification_code=code) # remove for production
    if user_query.scalar():
        user = user_query.first()
        login_user(user)
        data = user.to_json()
        data['status'] = 200
        return jsonify(data)
    else:
        return jsonify({"status": 401,
                        "reason": "Code is not correct"})

@app.route('/user_info', methods=['POST'])
def user_info():
    if current_user.is_authenticated:
        resp = {"result": 200,
                "data": current_user.to_json()}
    else:
        resp = {"result": 401,
                "data": {"message": "user no login"}}
    return jsonify(**resp)

@app.route("/", methods=["GET"])
def home():
    return render_template(
        "index.html",
        polly_api_key=os.getenv('POLLY_API_KEY'),
        google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY')
    )


if __name__ == "__main__":
    app.run(port=9000, debug=True)
