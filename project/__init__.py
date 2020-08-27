import json
import os
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt  # generate the hash-encoding for users' password
from flask_login import LoginManager

app = Flask(__name__)
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, 'config.json')
parameters = json.load(open(json_url, 'r'))["param"]  # loading configurable parameters' values from config.json file
# with open('config.json', 'r') as file:
#     parameters = json.load(file)["param"]

if parameters['server_local'] == "True":
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_URI']  # local host
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['host_URI']  # professional hosting

# self generated in console (import secrets and secrets.token_hex(20))
app.config['SECRET_KEY'] = parameters['secret_key']  # used for modifying cookies, cross sign attack request etc.
db = SQLAlchemy(app)  # initialize SQLAlchemy

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # for unauthorized access redirect to this url function
login_manager.login_message_category = 'info'  # bootstrap message category

app.config.update(  # configuring mail
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME=parameters['Mail_User_Name'],
    MAIL_PASSWORD=parameters['Mail_User_Password']
)
mail = Mail(app)  # initializing mail

# to avoid circular import error with import app in route.py place it after the full __init__.py initialization
from project import route
