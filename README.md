# Crisis Profile

Crisis Profile aims to provide 911 and crisis hotline call takers, first responders, and healthcare professionals specific information to de-escalate people in crisis. After a crisis, Crisis Profile can be used to coordinate mental health services.

## Installation

Create keys.sh

```
export SECRET_KEY="XXXXXXXX" 
export DEV_DATABASE_URL="postgresql+psycopg2://xxx:xxx@localhost/crisisprofile"
export MAILGUN_API_KEY="XXXXXXXX"
export API_EMAIL_DOMAIN_NAME="XXXXXXXX"
export APP_SETTINGS="config.StagingConfig"
```

Run

```
python3 -m pip -r requirements.py
sudo apt-get install flask
flask db upgrade
source keys.sh; flask run
```


