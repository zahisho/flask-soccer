import json

from app import db
from app.models import Team
from flask import url_for

from abstract_test_api import AbstractAPITestCase


class TeamAPITestCase(AbstractAPITestCase):
  def test_new_team(self):
    # try protected URL
    response = self.client.post(
        url_for('api.new_team'),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': 5000000}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'Authorization Required')
    self.assertTrue(json_response['description'] ==
                    'Request does not contain an access token')

    t_user = self.create_test_user()
    # authenticate with normal user
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])

    # try forbidden URL
    response = self.client.post(
        url_for('api.new_team'),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': 5000000}),
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

    # try register new team without name
    response = self.client.post(
        url_for('api.new_team'),
        data=json.dumps({'country': 'Argelia',
                         'wallet': 5000000}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description']
                    == '\'name\' is a required property')

    # try register new team with negative wallet
    response = self.client.post(
        url_for('api.new_team'),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': -5}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'].endswith(
        'is less than the minimum of 0'))

    # try register new team with non number user_id
    response = self.client.post(
        url_for('api.new_team'),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': 5000000,
                         'user_id': '1'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is not of type \'number\''))

    # try register new team with unexistent user_id
    response = self.client.post(
        url_for('api.new_team'),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': 5000000,
                         'user_id': 0}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 409)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'conflict')
    self.assertTrue(
        json_response['description'].endswith('user doesn\'t exist'))

    # register new team
    response = self.client.post(
        url_for('api.new_team'),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': 5000000}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 201)

    db.session.delete(t_user)
    db.session.delete(a_user)
    db.session.commit()

  def test_edit_team(self):
    team = Team(name='new_team', country='Argelia', wallet=5000000)
    db.session.add(team)
    db.session.commit()

    # try protected URL
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': 5000000}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'Authorization Required')
    self.assertTrue(json_response['description'] ==
                    'Request does not contain an access token')

    t_user = self.create_test_user()
    # authenticate with normal user
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])

    # try to edit team without being owner
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'name': 'new_team',
                         'country': 'Argelia',
                         'wallet': 5000000}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description'] == 'cannot edit this team')

    # set team's owner
    team.user_id = t_user.id
    db.session.add(team)
    db.session.commit()

    # try to edit team's owner
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'user_id': 2}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description']
                    == 'cannot change team\'s owner')

    # try to edit team's wallet
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'wallet': 0}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description']
                    == 'cannot update team\'s wallet')

    # edit team's accepted fields
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'country': 'Spain', 'name': 'my_team'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['country'] == 'Spain')
    self.assertTrue(json_response['name'] == 'my_team')

    a_user = self.create_admin_user()
    # authenticate with admin user
    jwt_token = self.get_access_token(
        self.admin_user['username'], self.admin_user['password'])

    # try edit team with negative wallet
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'wallet': -5}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'].endswith(
        'is less than the minimum of 0'))

    # try edit team with non number user_id
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'user_id': '1'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(
        json_response['description'].endswith('is not of type \'number\''))

    # try to set inexistent user to team
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'user_id': 0}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 409)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'conflict')
    self.assertTrue(json_response['description'] == 'user doesn\'t exist')

    # edit all team's fields
    response = self.client.put(
        url_for('api.edit_team', id=team.id),
        data=json.dumps({'country': 'Argelia', 'name': 'admin_team',
                         'wallet': 1000, 'user_id': a_user.id}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['country'] == 'Argelia')
    self.assertTrue(json_response['name'] == 'admin_team')
    self.assertTrue(json_response['wallet'] == 1000)

    db.session.delete(t_user)
    db.session.delete(a_user)
    db.session.delete(team)
    db.session.commit()

  def test_delete_team(self):
    t_user = self.create_test_user()
    a_user = self.create_admin_user()

    team = Team(name='new_team', country='Argelia', wallet=5000000)
    db.session.add(team)
    db.session.commit()

    # try to delete team without authorization
    response = self.client.delete(
        url_for('api.delete_team', id=team.id),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)

    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])
    # try to delete team without necessary permissions
    response = self.client.delete(
        url_for('api.delete_team', id=team.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)

    jwt_token = self.get_access_token(
        self.admin_user['username'], self.admin_user['password'])
    # delete team as administrator
    response = self.client.delete(
        url_for('api.delete_team', id=team.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 204)

    # try to delete unexistent team
    response = self.client.delete(
        url_for('api.delete_team', id=team.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 404)

    db.session.delete(a_user)
    db.session.delete(t_user)
    db.session.commit()
