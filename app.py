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
from sqlalchemy.orm.attributes import flag_modified
from flask import current_app as app, flash, redirect, render_template, session
from flask_login import login_manager, login_required, logout_user

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
from flask_login import login_required
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


# init Alchemy Dumps
from flask_alchemydumps import AlchemyDumps
alchemydumps = AlchemyDumps(app, db)

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

    def __init__(self, email_address):
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
    is_admin = db.Column(db.Boolean(), default=False)
    person_id = db.Column(UUID(as_uuid=True), db.ForeignKey('people.id'), nullable=True)
    job_title = db.Column(db.String(), nullable=True)
    organization = db.Column(db.String(), nullable=True)
    bookmarked_people = db.Column(JSON(), nullable=True)

    def __init__(self, email_address, emailed_verification_code, is_professional, person_id, job_title, agency):
        self.email_address = email_address
        self.emailed_verification_code = emailed_verification_code
        self.is_professional = is_professional
        self.person_id = person_id
        self.job_title = job_title
        self.agency = agency

    def to_json(self):      
        person_query = Person.query.filter_by(id=self.person_id)
        data = {"email_address": self.email_address}
        data['is_professional'] = self.is_professional
        data['is_admin'] = self.is_admin
        data['person_id'] = None
        data['bookmarked_people'] = []
        bookmarked_people = db.session.query(Person).filter(Person.id.in_(self.bookmarked_people if self.bookmarked_people else [])).all()
        if bookmarked_people:
            data['bookmarked_people'] = [{'id': person.id, 'first_name': person.first_name, 'middle_name': person.middle_name, 'last_name': person.last_name} for person in bookmarked_people]

        if person_query.scalar():
            person = person_query.first()
            data['person_id'] = person.id
        return data

    def is_authenticated(self):
        return True

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False          

    def get_id(self):         
        return str(self.id)    

import uuid
class Person(db.Model):
    __tablename__ = 'people'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=sqlalchemy.text("uuid_generate_v4()"), unique=True)
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
    coping_techniques_to_use_before_calling_for_help = db.Column(db.String(), nullable=True)
    mental_health_treatment_summary = db.Column(db.String(), nullable=True)
    medication_notes = db.Column(db.String(), nullable=True)
    preferred_psychiatric_inpatient_facility = db.Column(db.String(), nullable=True)
    pets = db.Column(JSON(), nullable=True)
    promises_made_to_person = db.Column(JSON(), nullable=True)
    stressors = db.Column(JSON(), nullable=True)
    diagnoses = db.Column(JSON(), nullable=True)
    bio = db.Column(db.String(), nullable=True)

    def __init__(self, first_name, middle_name, last_name, birthdate):
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        from datetime import datetime
        self.date_of_birth = datetime.strptime(birthdate, "%m/%d/%Y").date()

    def to_json(self):
        data = {}
        data['id'] = self.id
        data['first_name'] = self.first_name
        data['middle_name'] = self.middle_name
        data['last_name'] = self.last_name
        data['preferred_name'] = self.preferred_name
        data['preferred_gender_pronouns'] = self.preferred_gender_pronouns
        data['date_of_birth'] = self.date_of_birth.strftime("%B %-d, %Y")
        data['age'] = calculate_age(self.date_of_birth.date())
        data['contacts'] = self.contacts
        data['persons_phone_numbers'] = self.persons_phone_numbers
        data['current_physical_living_address_1'] = self.current_physical_living_address_1
        data['current_physical_living_address_2'] = self.current_physical_living_address_2
        data['current_physical_living_address_city'] = self.current_physical_living_address_city
        data['current_physical_living_address_state'] = self.current_physical_living_address_state
        data['current_physical_living_address_zip_code'] = self.current_physical_living_address_zip_code
        data['coping_techniques_to_use_before_calling_for_help'] = self.coping_techniques_to_use_before_calling_for_help
        data['medications'] = self.medications
        data['safety_information'] = self.safety_information
        data['mental_health_treatment_summary'] = self.mental_health_treatment_summary 
        data['medication_notes'] = self.medication_notes
        data['appointments'] = self.appointments
        return data



@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)




@app.route("/send_login_email", methods=["POST"])
def send_login_email():
    email_address = request.form['email']
    if os.environ.get('IS_DEV_AUTO_LOGIN', False) == 'true':
        email_address = os.environ.get('AUTO_LOGIN_EMAIL')
    verification_token = create_random_string()
    does_email_exist = db.session.query(User.id).filter_by(email_address=email_address).scalar() is not None
    if does_email_exist:
        user = User.query.filter_by(email_address=email_address).first()
        user.emailed_verification_code = verification_token
        user.datetime_verification_code_created = datetime.datetime.utcnow()
    else:
        user = User(email_address, verification_token, None, None, None, None)
        db.session.add(user)
    user.is_professional = True if ApprovedWorkEmailAddressDomain.query.filter_by(email_address_domain=email_address[email_address.index('@')+1:]).scalar() else False
    if ApprovedWorkEmailAddress.query.filter_by(email_address=email_address).scalar():
        user.is_professional = True
    db.session.commit()
    if os.environ.get('IS_DEV_AUTO_LOGIN', False) == 'true':
        return jsonify("email sent")
    email = requests.post(
        "https://api.mailgun.net/v3/%s/messages" % (os.getenv("API_EMAIL_DOMAIN_NAME")),
        auth=("api", "%s" % (os.getenv("MAILGUN_API_KEY"))),
        data={
            "from": "Crisis Profile <no-reply@%s>"
            % (os.getenv("API_EMAIL_DOMAIN_NAME")),
            "to": ["%s" % (request.form.get('email'))],
            "subject": "Login code for Crisis Profile",
            "text": 'Hi! This is a login email for logging into Crisis Profile. Enter the code: %s on https://crisisprofile.com'
            % (
                verification_token,
            ),
        },
    ).text
    return jsonify("email sent")

@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()

@app.route('/get_profile', methods=['GET'])
@login_required
def get_profile():
    person_query = Person.query.filter_by(id=request.args['person_id']).first()
    return jsonify(person_query.to_json())

@app.route('/get_approved_professionals', methods=['GET'])
@login_required
def get_approved_professionals():
    data = {'domains': [row.email_address_domain for row in ApprovedWorkEmailAddressDomain.query.all()]}
    data['email_addresses'] = [row.email_address for row in ApprovedWorkEmailAddress.query.all()]
    return jsonify(data)

@app.route('/bookmark_this_person', methods=['POST'])
@login_required
def bookmark_this_person():
    user = current_user
    if not user.bookmarked_people:
        user.bookmarked_people = []
    user.bookmarked_people.append(request.form['person_uuid'])
    flag_modified(user, "bookmarked_people")
    db.session.commit()
    return jsonify({'successful': True})

@app.route('/edit_basic_information', methods=['POST'])
@login_required
def edit_basic_information():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    person.first_name = request.form['first_name']
    person.middle_name = request.form['middle_name']
    person.last_name = request.form['last_name']
    person.preferred_name = request.form['preferred_name']
    person.preferred_gender_pronouns = request.form['preferred_gender_pronouns']
    person.current_physical_living_address_1 = request.form['current_physical_living_address_1']
    person.current_physical_living_address_2 = request.form['current_physical_living_address_2']
    person.current_physical_living_address_city = request.form['current_physical_living_address_city']
    person.current_physical_living_address_state = request.form['current_physical_living_address_state']
    person.current_physical_living_address_zip_code = request.form['current_physical_living_address_zip_code']
    person.persons_phone_numbers = [{"phone_number": request.form["phone_number_0"], "type": request.form["phone_number_type_0"]}]
    above_elements = {}
    above_elements['first_name'] = person.first_name
    above_elements['middle_name'] = request.form['middle_name']
    above_elements['last_name'] = request.form['last_name']
    above_elements['preferred_name'] = request.form['preferred_name']
    above_elements['preferred_gender_pronouns'] = request.form['preferred_gender_pronouns']
    above_elements['current_physical_living_address_1'] = request.form['current_physical_living_address_1']
    above_elements['current_physical_living_address_2'] = request.form['current_physical_living_address_2']
    above_elements['current_physical_living_address_city'] = request.form['current_physical_living_address_city']
    above_elements['current_physical_living_address_state'] = request.form['current_physical_living_address_state']
    above_elements['current_physical_living_address_zip_code'] = request.form['current_physical_living_address_zip_code']
    above_elements['persons_phone_numbers'] = person.persons_phone_numbers
    flag_modified(person, "persons_phone_numbers")
    db.session.commit()
    return jsonify(above_elements)

@app.route('/edit_safety_information', methods=['POST'])
@login_required
def edit_safety_information():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    person.safety_information = request.form['safety_information']
    db.session.commit()
    return jsonify({'safety_information': person.safety_information})
from sqlalchemy import and_, or_, not_

@app.route('/search', methods=['GET'])
@login_required
def search():
    people = [{'id': person.id, 'first_name': person.first_name, 'middle_name': person.middle_name, 'last_name': person.last_name} for person in Person.query.filter(and_(Person.first_name.ilike(request.args['first_name']), Person.last_name.ilike(request.args['last_name'])))]
    return jsonify(people)


@app.route('/edit_precall_coping', methods=['POST'])
@login_required
def edit_precall_coping():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    person.coping_techniques_to_use_before_calling_for_help = request.form['coping_techniques_to_use_before_calling_for_help']
    db.session.commit()
    return jsonify({'coping_techniques_to_use_before_calling_for_help': person.coping_techniques_to_use_before_calling_for_help})

@app.route('/edit_mental_health_treatment', methods=['POST'])
@login_required
def edit_mental_health_treatment():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    person.mental_health_treatment_summary = request.form['mental_health_treatment_summary']
    db.session.commit()
    return jsonify({'mental_health_treatment_summary': person.mental_health_treatment_summary})

@app.route('/edit_medication_notes', methods=['POST'])
@login_required
def edit_medication_notes():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    person.medication_notes = request.form['medication_notes']
    db.session.commit()
    return jsonify({'medication_notes': person.medication_notes})

@app.route('/add_person', methods=['POST'])
@login_required
def add_person():
    print('birth date', request.form['birth_date'])
    person = Person(request.form['first_name'], request.form['middle_name'], request.form['last_name'], request.form['birth_date'])
    db.session.add(person)
    db.session.commit()

    return jsonify({'person_uuid': person.id})


@app.route('/add_medication', methods=['POST'])
@login_required
def add_medication():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    medications = person.medications
    if not medications:
        medications = []
    medications.append({'name': request.form['name'], 'tablet_size': request.form['tablet_size'], 'instructions': request.form['instructions']})
    person.medications = medications
    flag_modified(person, "medications")
    db.session.commit()
    return jsonify(medications)

@app.route('/delete_medication', methods=['POST'])
@login_required
def delete_medication():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    medications = person.medications
    del medications[int(request.form['index'])]
    person.medications = medications
    flag_modified(person, "medications")
    db.session.commit()
    return jsonify(medications)


@app.route('/delete_appointment', methods=['POST'])
@login_required
def delete_appointment():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    appointments = person.appointments
    del appointments[int(request.form['index'])]
    person.appointments = appointments
    flag_modified(person, "appointments")
    db.session.commit()
    return jsonify(appointments)


@app.route('/add_appointment', methods=['POST'])
@login_required
def add_appointment():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    appointments = person.appointments
    if not appointments:
        appointments = []
    appointments.append({'date': request.form['date'], 'start_time': request.form['start_time'], 'stop_time': request.form['stop_time'], 'what': request.form['what'], 'notes': request.form['notes']})

    person.appointments = appointments
    flag_modified(person, "appointments")
    db.session.commit()
    return jsonify(appointments)

@app.route('/delete_contact', methods=['POST'])
@login_required
def delete_contact():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    contacts = person.contacts
    del contacts[int(request.form['index'])]
    person.contacts = contacts
    flag_modified(person, "contacts")
    db.session.commit()
    return jsonify(contacts)    

@app.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    contacts = person.contacts
    contacts.append({'name': request.form['name'], 'relationship': request.form['relationship'], 'phone_number': request.form['phone_number'], 'email': request.form['email'], 'notes': request.form['notes']})
    person.contacts = contacts
    flag_modified(person, "contacts")
    db.session.commit()
    return jsonify(contacts)

@app.route('/edit_contact', methods=['POST'])
@login_required
def edit_contact():
    person_uuid = request.form['person_uuid']
    person = Person.query.get(person_uuid)
    contacts = person.contacts
    contacts[int(request.form['index'])] = {'name': request.form['name'], 'relationship': request.form['relationship'], 'phone_number': request.form['phone_number'], 'email': request.form['email'], 'notes': request.form['notes'], 'is_professional': True if request.form['is_professional'] == 'true' else False}
    person.contacts = contacts
    flag_modified(person, "contacts")
    db.session.commit()
    return jsonify(contacts)    

@app.route('/login', methods=['POST'])
def login():
    if os.environ.get('IS_DEV_AUTO_LOGIN', False) == 'true':
        email_address = os.environ.get("AUTO_LOGIN_EMAIL", "")
        user_query = User.query.filter_by(email_address=email_address)
    else:
        info = request.form
        email_address = info['email_address'].strip()
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    if session.get('was_once_logged_in'):
        # prevent flashing automatically logged out message
        del session['was_once_logged_in']
    flash('You have successfully logged yourself out.')
    return redirect('/')

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

@app.route('/add_professional_domain', methods=["POST"])
@login_required
def add_professional_domain():
    domain = ApprovedWorkEmailAddressDomain(request.form['domain'])
    db.session.add(domain)
    db.session.commit()
    return jsonify([row.email_address_domain for row in ApprovedWorkEmailAddressDomain.query.all()])

@app.route('/add_professional_email_address', methods=["POST"])
@login_required
def add_professional_email_address():
    email = ApprovedWorkEmailAddress(request.form['email'])
    db.session.add(email)
    db.session.commit()
    return jsonify([row.email_address for row in ApprovedWorkEmailAddress.query.all()])


if __name__ == "__main__":
    app.run(port=9000, debug=True)
