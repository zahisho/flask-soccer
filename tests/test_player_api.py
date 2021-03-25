import json

from app import db
from app.models import Player, Team
from flask import url_for

from abstract_test_api import AbstractAPITestCase


class PlayerAPITestCase(AbstractAPITestCase):
  def test_new_player(self):
    t_team = Team(name='test_team', country='Spain', wallet=0)
    db.session.add(t_team)
    db.session.commit()

    # try protected URL
    response = self.client.post(
        url_for('api.new_player'),
        data=json.dumps({'name': 'Peter',
                         'lastname': 'Smith',
                         'country': 'Argelia',
                         'value': 1000000,
                         'age': 27,
                         'position': 'Defender'}),
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
        url_for('api.new_player'),
        data=json.dumps({'name': 'Peter',
                         'lastname': 'Smith',
                         'country': 'Argelia',
                         'value': 1000000,
                         'age': 27,
                         'position': 'Defender'}),
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

    # try to register new player without name
    response = self.client.post(
        url_for('api.new_player'),
        data=json.dumps({'lastname': 'Smith',
                         'country': 'Argelia',
                         'value': 1000000,
                         'age': 27,
                         'team_id': 0,
                         'position': 'Defender'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description']
                    == '\'name\' is a required property')

    # try to register new player with negative age
    response = self.client.post(
        url_for('api.new_player'),
        data=json.dumps({'name': 'Peter',
                         'lastname': 'Smith',
                         'country': 'Argelia',
                         'value': 1000000,
                         'age': -1,
                         'team_id': 0,
                         'position': 'Defender'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'].endswith(
        'is less than the minimum of 0'))

    # try to register new player with unknown team
    response = self.client.post(
        url_for('api.new_player'),
        data=json.dumps({'name': 'Peter',
                         'lastname': 'Smith',
                         'country': 'Argelia',
                         'value': 1000000,
                         'age': 27,
                         'team_id': 0,
                         'position': 'Defender'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 409)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'conflict')
    self.assertTrue(json_response['description'] == 'team doesn\'t exist')

    # register new player
    response = self.client.post(
        url_for('api.new_player'),
        data=json.dumps({'name': 'Peter',
                         'lastname': 'Smith',
                         'country': 'Argelia',
                         'value': 1000000,
                         'age': 27,
                         'team_id': t_team.id,
                         'position': 'Defender'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 201)

    db.session.delete(t_user)
    db.session.delete(a_user)
    db.session.delete(t_team)
    db.session.commit()

  def test_edit_player(self):
    player = Player(name='Peter', lastname='Smith',
                    country='Argelia', value=1000000, age=28, position='Defender')
    db.session.add(player)
    db.session.commit()

    # try protected URL
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'name': 'Juan',
                         'lastname': 'Reyes',
                         'country': 'Spain',
                         'value': 5000000,
                         'age': 28}),
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

    # try to edit player without being owner
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'name': 'Juan',
                         'lastname': 'Reyes',
                         'country': 'Spain',
                         'value': 5000000,
                         'age': 28}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description'] == 'cannot edit this player')

    # set player's owner
    team = Team(name='new_team', wallet=5000000,
                country='Spain', user_id=t_user.id)
    team.players.append(player)
    db.session.add(team)
    db.session.commit()

    # try to edit player's team
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'team_id': 0}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description']
                    == 'cannot change player\'s team')

    # try to edit player's value
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'value': 5000000}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description']
                    == 'cannot update player\'s value')

    # try to edit player's age
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'age': 26}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description']
                    == 'cannot update player\'s age')

    # edit player's accepted fields
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'name': 'Juan',
                         'lastname': 'Reyes',
                         'country': 'Spain',
                         'position': 'Attacker'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['country'] == 'Spain')
    self.assertTrue(json_response['name'] == 'Juan')
    self.assertTrue(json_response['lastname'] == 'Reyes')
    self.assertTrue(json_response['position'] == 'Attacker')

    a_user = self.create_admin_user()
    # authenticate with admin user
    jwt_token = self.get_access_token(
        self.admin_user['username'], self.admin_user['password'])

    # try to set negative age to player
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'age': -1}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'].endswith(
        'is less than the minimum of 0'))

    # try to set non boolean offer
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'offer': 1}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'].endswith(
        'is not of type \'boolean\''))

    # try to set inexistent team to player
    response = self.client.put(
        url_for('api.edit_player', id=player.id),
        data=json.dumps({'team_id': 0}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 409)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'conflict')
    self.assertTrue(json_response['description'] == 'team doesn\'t exist')

    team2 = Team(name='new_team2', wallet=5000000,
                 country='Russia')
    db.session.add(team2)
    db.session.commit()

    # edit all player's fields
    response = self.client.put(
        url_for('api.edit_player', id=team.id),
        data=json.dumps({'name': 'Marcos',
                         'lastname': 'Smith',
                         'country': 'Brazil',
                         'team_id': team2.id,
                         'age': 26,
                         'value': 5000000,
                         'position': 'Defender'}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['country'] == 'Brazil')
    self.assertTrue(json_response['name'] == 'Marcos')
    self.assertTrue(json_response['lastname'] == 'Smith')
    self.assertTrue(json_response['age'] == 26)
    self.assertTrue(json_response['value'] == 5000000)
    self.assertTrue(json_response['position'] == 'Defender')

    db.session.delete(t_user)
    db.session.delete(a_user)
    db.session.delete(player)
    db.session.delete(team)
    db.session.delete(team2)
    db.session.commit()

  def test_delete_player(self):
    t_user = self.create_test_user()
    a_user = self.create_admin_user()

    player = Player(name='Peter', lastname='Smith',
                    country='Argelia', value=1000000, age=23, position='Defender')
    db.session.add(player)
    db.session.commit()

    # try to delete player without authorization
    response = self.client.delete(
        url_for('api.delete_player', id=player.id),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)

    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])
    # try to delete player without necessary permissions
    response = self.client.delete(
        url_for('api.delete_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)

    jwt_token = self.get_access_token(
        self.admin_user['username'], self.admin_user['password'])
    # delete player as administrator
    response = self.client.delete(
        url_for('api.delete_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 204)

    # try to delete unexistent player
    response = self.client.delete(
        url_for('api.delete_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 404)

    db.session.delete(a_user)
    db.session.delete(t_user)
    db.session.commit()
