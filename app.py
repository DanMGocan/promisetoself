# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

# Internal imports
from db import init_db_command
from user import User

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Google config #
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# Find out what URL to hit to get tokens that allow you to ask for
# things on behalf of a user
google_provider_cfg = get_google_provider_cfg()
token_endpoint = google_provider_cfg["token_endpoint"]

##########
# Routes #
##########
@app.route("/")
def index():
    if current_user.is_authenticated:
        return (
            f"<p>Hello, {current_user.name}! You're logged in! Email: {current_user.email}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{current_user.profile_pic}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'
            )
    else:
        return '<a class="button" href="/login">Google Login</a>'
    
@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

print(os.environ["GOOGLE_CLIENT_ID"])

if __name__ == "__main__":
    app.run(ssl_context="adhoc")