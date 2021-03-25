import json

from app import db
from flask import url_for

from abstract_test_api import AbstractAPITestCase


class APISecurityTestCase(AbstractAPITestCase):
  def test_authentication(self):
    t_user = self.create_test_user()
    # authenticate with bad password
    response = self.client.post(
        self.app.config['JWT_AUTH_URL_RULE'],
        data=json.dumps({'username': self.test_user['username'],
                         'password': 'wrongpassword'}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'Bad Request')
    self.assertTrue(json_response['description'] == 'Invalid credentials')

    # authenticate with correct password
    response = self.client.post(
        self.app.config['JWT_AUTH_URL_RULE'],
        data=json.dumps({'username': self.test_user['username'],
                         'password': self.test_user['password']}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertIsNotNone(json_response['access_token'])

    db.session.delete(t_user)
    db.session.commit()

  def test_protected_URL(self):
    # access protected URL without authorization
    response = self.client.get(
        url_for('api.get_users'),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'Authorization Required')
    self.assertTrue(json_response['description'] ==
                    'Request does not contain an access token')

    t_user = self.create_test_user()
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])
    # access protected URL with authorization
    response = self.client.get(
        url_for('api.get_users'),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(type(json_response) == list)

    db.session.delete(t_user)
    db.session.commit()

  def test_user_registration(self):
    # try to register new user without email
    response = self.client.post(
        url_for('api.register_user'),
        data=json.dumps({'password': 'pass1234'}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description']
                    == '\'username\' is a required property')

    # try to register new user with incorrect email
    response = self.client.post(
        url_for('api.register_user'),
        data=json.dumps({'username': 'new_user',
                         'password': 'pass1234'}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is not a \'email\''))

    # try to register new user with a short password
    response = self.client.post(
        url_for('api.register_user'),
        data=json.dumps({'username': 'new_user@example.com',
                         'password': 'pass12'}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is too short'))

    # register new user
    response = self.client.post(
        url_for('api.register_user'),
        data=json.dumps({'username': 'new_user@example.com',
                         'password': 'pass1234'}),
        headers=self.get_api_headers()
    )
    new_user = json.loads(response.data.decode('utf-8'))
    self.assertTrue(response.status_code == 201)

    # try to register with an existent email
    response = self.client.post(
        url_for('api.register_user'),
        data=json.dumps({'username': 'new_user@example.com',
                         'password': 'pass1234'}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 409)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'conflict')
    self.assertTrue(json_response['description'] == 'email already registered')

    # authenticate with new user
    response = self.client.post(
        self.app.config['JWT_AUTH_URL_RULE'],
        data=json.dumps({'username': 'new_user@example.com',
                         'password': 'pass1234'}),
        headers=self.get_api_headers()
    )
    jwt_token = json.loads(response.data.decode('utf-8'))['access_token']

    # get new user's team
    response = self.client.get(
        new_user['team'],
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    user_team = json.loads(response.data.decode('utf-8'))
    self.assertTrue(user_team['wallet'] == 5000000)
    self.assertTrue(user_team['value'] == 20000000)

    # get new user's players
    response = self.client.get(
        new_user['players'],
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    user_players = json.loads(response.data.decode('utf-8'))
    self.assertTrue(len(user_players) == 20)
    for p in user_players:
      self.assertTrue(p['value'] == 1000000)
