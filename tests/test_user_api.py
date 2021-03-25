import json

import jwt
from app import db
from flask import url_for

from abstract_test_api import AbstractAPITestCase


class UserAPITestCase(AbstractAPITestCase):
  def test_new_user(self):
    t_user = self.create_test_user()
    # authenticate with normal user
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])

    # try forbidden URL
    response = self.client.post(
        url_for('api.new_user'),
        data=json.dumps({'username': 'new_user@example.com',
                         'password': 'pass123'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description'] == 'insufficient permissions')

    a_user = self.create_admin_user()
    # authenticate with admin user
    jwt_token = self.get_access_token(
        self.admin_user['username'], self.admin_user['password'])

    # try register new user without email
    response = self.client.post(
        url_for('api.new_user'),
        data=json.dumps({'password': 'pass123'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description']
                    == '\'username\' is a required property')

    # try register new user with incorrect email
    response = self.client.post(
        url_for('api.new_user'),
        data=json.dumps({'username': 'new_user2',
                         'password': 'pass123'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is not a \'email\''))

    # try register new user with short password
    response = self.client.post(
        url_for('api.new_user'),
        data=json.dumps({'username': 'new_user2@example.com',
                         'password': 'pass123'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is too short'))

    # try register new user with non number role_id
    response = self.client.post(
        url_for('api.new_user'),
        data=json.dumps({'username': 'new_user2@example.com',
                         'password': 'pass1234',
                         'role_id': 'algo'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is not of type \'number\''))

    # register new user
    response = self.client.post(
        url_for('api.new_user'),
        data=json.dumps({'username': 'new_user2@example.com',
                         'password': 'pass1234'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 201)

    db.session.delete(t_user)
    db.session.delete(a_user)
    db.session.commit()

  def test_edit_user(self):
    t_user = self.create_test_user()
    # authenticate with normal user
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])
    user_id = jwt.decode(jwt_token, self.app.config['SECRET_KEY'])['identity']

    # try edit other user
    response = self.client.put(
        url_for('api.edit_user', id=user_id+1),
        data=json.dumps({'username': 'test_user@example.com',
                         'password': 'pass1234'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description'] == 'cannot edit other user')

    # edit current user
    response = self.client.put(
        url_for('api.edit_user', id=user_id),
        data=json.dumps({'username': 'test_user@example.com',
                         'password': 'pass1234'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)

    a_user = self.create_admin_user()
    # authenticate as administrator
    jwt_token = self.get_access_token(
        self.admin_user['username'], self.admin_user['password'])

    # try edit user with incorrect email
    response = self.client.put(
        url_for('api.edit_user', id=user_id),
        data=json.dumps({'username': 'new_user2',
                         'password': 'pass123'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is not a \'email\''))

    # try edit user with short password
    response = self.client.put(
        url_for('api.edit_user', id=user_id),
        data=json.dumps({'username': 'new_user2@example.com',
                         'password': 'pass123'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is too short'))

    # try edit user with non number role_id
    response = self.client.put(
        url_for('api.edit_user', id=user_id),
        data=json.dumps({'username': 'new_user2@example.com',
                         'password': 'pass1234',
                         'role_id': 'algo'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is not of type \'number\''))

    # edit test user
    response = self.client.put(
        url_for('api.edit_user', id=user_id),
        data=json.dumps({'username': 'test_user@example.com',
                         'password': 'pass1234'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)

    db.session.delete(t_user)
    db.session.delete(a_user)
    db.session.commit()

  def test_delete_user(self):
    t_user = self.create_test_user()
    a_user = self.create_admin_user()

    # try to delete user without authorization
    response = self.client.delete(
        url_for('api.delete_user', id=t_user.id),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)

    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])
    # try to delete user without necessary permissions
    response = self.client.delete(
        url_for('api.delete_user', id=t_user.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)

    jwt_token = self.get_access_token(
        self.admin_user['username'], self.admin_user['password'])
    # try to delete user as administrator
    response = self.client.delete(
        url_for('api.delete_user', id=t_user.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 204)

    db.session.delete(a_user)
    db.session.commit()
