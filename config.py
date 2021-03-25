import os
from datetime import timedelta


class Config:
  SECRET_KEY = os.environ.get(
      'SECRET_KEY') or '3d6f45a5fc12445dbac2f59c3b6c7cb1'
  SQLALCHEMY_COMMIT_ON_TEARDOWN = True
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SQLALCHEMY_RECORD_QUERIES = True
  JWT_EXPIRATION_DELTA = timedelta(minutes=600)

  @staticmethod
  def init_app(app):
    pass


class DevelopmentConfig(Config):
  DEBUG = True
  SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
      'mysql://user:password@localhost/soccer_online'


class TestingConfig(Config):
  TESTING = True
  SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
      'mysql://user:password@localhost/test_soccer_online'


config = {
    'development': DevelopmentConfig,
    'test': TestingConfig,

    'default': DevelopmentConfig
}
