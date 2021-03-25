import json
import unittest

from app import create_app, db
from app.models import Role, User


class AbstractAPITestCase(unittest.TestCase):
  def setUp(self):
    self.app = create_app('test')
    self.app_context = self.app.app_context()
    self.app_context.push()
    db.create_all()
    Role.create_roles()
    self.test_user = {
        'username': 'test_user@example.com',
        'password': 'pass123'
    }
    self.admin_user = {
        'username': 'admin_user@example.com',
        'password': 'pass123'
    }
    self.client = self.app.test_client()

  def tearDown(self):
    db.session.remove()
    db.drop_all()
    self.app_context.pop()

  def get_api_headers(self, jwt_token=None):
    if jwt_token:
      return {
          'Authorization': 'JWT ' + jwt_token,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
      }
    else:
      return {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
      }

  def create_test_user(self):
    role_user = Role.query.filter_by(name='User').first()

    # add a user
    u = User(email=self.test_user['username'],
             password=self.test_user['password'], role_id=role_user.id)
    db.session.add(u)
    db.session.commit()

    return u

  def create_admin_user(self):
    role_user = Role.query.filter_by(name='Administrator').first()

    # add a user
    u = User(email=self.admin_user['username'],
             password=self.admin_user['password'], role_id=role_user.id)
    db.session.add(u)
    db.session.commit()

    return u

  def get_access_token(self, username, password):
    response = self.client.post(
        self.app.config['JWT_AUTH_URL_RULE'],
        data=json.dumps({'username': username,
                         'password': password}),
        headers=self.get_api_headers()
    )
    json_response = json.loads(response.data.decode('utf-8'))

    return json_response['access_token']
