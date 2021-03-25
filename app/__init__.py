from config import config
from flask import Flask
from flask_jwt import JWT
from flask_sqlalchemy import SQLAlchemy

from .authentication import authenticate, identity

db = SQLAlchemy()


def create_app(config_name):
  app = Flask(__name__)
  app.config.from_object(config[config_name])
  config[config_name].init_app(app)

  db.init_app(app)

  JWT(app, authenticate, identity)

  from .api import api as api_blueprint
  app.register_blueprint(api_blueprint, url_prefix='/api')

  return app
