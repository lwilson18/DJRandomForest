from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

application = Flask(__name__)
application.config.from_object(Config)

db = SQLAlchemy(application)