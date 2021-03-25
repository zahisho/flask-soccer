import json

from app import db
from app.models import Player, Team
from flask import url_for

from abstract_test_api import AbstractAPITestCase


class MarketAPITestCase(AbstractAPITestCase):
  def test_get_players_market(self):
    pl1 = Player(name='Peter', lastname='Smith', country='Spain',
                 value=1000000, price=1000100, age=22, offer=True, position='Defender')
    pl2 = Player(name='Sam', lastname='Reynolds', country='Argelia',
                 value=1000000, price=1020300, age=18, offer=True, position='Attacker')
    pl3 = Player(name='Peter', lastname='Carter', country='Spain',
                 value=1000000, price=1119400, age=32, offer=True, position='Goalkeeper')

    t1 = Team(name='Barcelona', country='Spain', wallet=1000000)
    t2 = Team(name='Bayern', country='Germany', wallet=2000000)

    t1.players.append(pl1)
    t1.players.append(pl2)
    t2.players.append(pl3)

    db.session.add(t1)
    db.session.add(t2)

    # try to request in market without authorization
    response = self.client.get(
        url_for('api.get_players_market'),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)

    t_user = self.create_test_user()
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])

    # request in market with authorization
    response = self.client.get(
        url_for('api.get_players_market'),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(len(json_response) == 3)

    # request in market filter by team name
    response = self.client.get(
        url_for('api.get_players_market'),
        query_string={'team': 'Barcelona'},
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(len(json_response) == 2)

    # request in market filter by team name and player's name
    response = self.client.get(
        url_for('api.get_players_market'),
        query_string={'team': 'Barcelona', 'name': 'peter'},
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(len(json_response) == 1)

    # request in market filter by price
    response = self.client.get(
        url_for('api.get_players_market'),
        query_string={'minPrice': 1000000, 'maxPrice': 1010000},
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 200)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(len(json_response) == 1)

    db.session.delete(t1)
    db.session.delete(t2)
    db.session.delete(pl1)
    db.session.delete(pl2)
    db.session.delete(pl3)
    db.session.commit()

  def test_offer_player(self):
    player = Player(name='Peter', lastname='Smith',
                    country='Spain', value=1000000, age=22, position='Defender')

    team = Team(name='Barcelona', country='Spain', wallet=1000000)
    team.players.append(player)
    db.session.add(team)
    db.session.commit()

    # try to offer in market without authorization
    response = self.client.post(
        url_for('api.offer_player', id=player.id),
        data=json.dumps({'price': player.value*3}),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)

    t_user = self.create_test_user()
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])

    # try to offer a player not owned
    response = self.client.post(
        url_for('api.offer_player', id=player.id),
        data=json.dumps({'price': player.value*3}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 403)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'forbidden')
    self.assertTrue(json_response['description'] == 'cannot edit this player')

    t_user.team = team
    db.session.add(t_user)
    db.session.commit()

    # try to offer a player without a price
    response = self.client.post(
        url_for('api.offer_player', id=player.id),
        data=json.dumps({}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'] ==
                    '\'price\' is a required property')

    # try to offer a player with a negative price
    response = self.client.post(
        url_for('api.offer_player', id=player.id),
        data=json.dumps({'price': -1}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'].endswith(
        'is less than the minimum of 0'))

    # try to offer a player by a price over 100% of value
    response = self.client.post(
        url_for('api.offer_player', id=player.id),
        data=json.dumps({'price': player.value*3}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'] ==
                    'player\'s price cannot be more that 100% of current value')

    # offer a player correctly
    response = self.client.post(
        url_for('api.offer_player', id=player.id),
        data=json.dumps({'price': player.value*1.1}),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 204)

    db.session.delete(player)
    db.session.delete(team)
    db.session.delete(t_user)
    db.session.commit()

  def test_buy_player(self):
    player = Player(name='Peter', lastname='Smith', country='Spain',
                    value=1000000, age=22, price=1000100, position='Attacker')

    t1 = Team(name='Barcelona', country='Spain', wallet=1000000)
    t1.players.append(player)
    db.session.add(t1)
    db.session.commit()

    # try to buy without authorization
    response = self.client.post(
        url_for('api.buy_player', id=player.id),
        headers=self.get_api_headers()
    )
    self.assertTrue(response.status_code == 401)

    t_user = self.create_test_user()
    jwt_token = self.get_access_token(
        self.test_user['username'], self.test_user['password'])

    # try to buy not offered player
    response = self.client.post(
        url_for('api.buy_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'] == 'player is not in market')

    player.offer = True
    db.session.add(player)
    db.session.commit()

    # try to buy without owning a team
    response = self.client.post(
        url_for('api.buy_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description'] == 'you don\'t own a team')

    t1.user = t_user
    db.session.add(t1)
    db.session.commit()

    # try to buy a player that already is owned
    response = self.client.post(
        url_for('api.buy_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description']
                    == 'this player is already yours')

    t1.user = None
    db.session.add(t1)
    db.session.commit()

    t2 = Team(name='Real Madrid', country='Spain', wallet=0, user=t_user)
    db.session.add(t2)
    db.session.commit()

    # try to buy a player without enough money
    response = self.client.post(
        url_for('api.buy_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 400)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'bad request')
    self.assertTrue(json_response['description']
                    == 'you don\'t have enough money to buy this player')

    t2.wallet = 2000000
    db.session.add(t2)
    db.session.commit()

    t2_wallet_old = t2.wallet
    t1_wallet_old = t1.wallet
    p_value_old = player.value

    # buy a player
    response = self.client.post(
        url_for('api.buy_player', id=player.id),
        headers=self.get_api_headers(jwt_token)
    )
    self.assertTrue(response.status_code == 204)
    self.assertTrue(t2.wallet == t2_wallet_old-player.price)
    self.assertTrue(t1.wallet == t1_wallet_old+player.price)
    self.assertTrue(player.value >= p_value_old*1.1)
    self.assertTrue(player.value <= p_value_old*2)
    self.assertFalse(player.offer)

    db.session.delete(player)
    db.session.delete(t1)
    db.session.delete(t2)
    db.session.delete(t_user)
