from flask import jsonify, request, url_for
from flask_jwt import current_identity, jwt_required

from .. import db
from ..models import Player, Team
from ..utils import update_player_price
from . import api
from .decorators import admin_required, validate_input
from .errors import conflict, forbidden, bad_request


@api.route('/players')
@jwt_required()
def get_players():
  players = Player.query.all()
  players = list(map(lambda p: p.to_json(), players))
  return jsonify(players)


@api.route('/players/<int:id>')
@jwt_required()
def get_player(id):
  player = Player.query.get_or_404(id)
  return jsonify(player.to_json())


@api.route('/players', methods=['POST'])
@jwt_required()
@admin_required()
@validate_input(json_schema={
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string'
        },
        'lastname': {
            'type': 'string'
        },
        'country': {
            'type': 'string'
        },
        'value': {
            'type': 'number',
            'minimum': 0
        },
        'age': {
            'type': 'number',
            'minimum': 0
        },
        'position': {
            'type': 'string'
        },
        'team_id': {
            'type': 'number'
        }
    },
    'required': ['name', 'lastname', 'country', 'value', 'age', 'position']
})
def new_player():
  json_player = request.json
  player = Player(name=json_player['name'], lastname=json_player['lastname'], country=json_player['country'],
                  value=json_player['value'], age=json_player['age'], position=json_player['position'])
  if 'team_id' in json_player:
    team = Team.query.get(json_player['team_id'])
    if team == None:
      return conflict('team doesn\'t exist')
    player.team_id = json_player['team_id']
  db.session.add(player)
  db.session.commit()

  return jsonify(player.to_json()), 201, {'Location': url_for('api.get_player', id=player.id, _external=True)}


@api.route('/players/<int:id>', methods=['PUT'])
@jwt_required()
@validate_input(json_schema={
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string'
        },
        'lastname': {
            'type': 'string'
        },
        'country': {
            'type': 'string'
        },
        'value': {
            'type': 'number',
            'minimum': 0
        },
        'age': {
            'type': 'number',
            'minimum': 0
        },
        'position': {
            'type': 'string'
        },
        'team_id': {
            'type': 'number'
        },
        'offer': {
            'type': 'boolean'
        },
        'price': {
            'type': 'number',
            'minimum': 0
        }
    }
})
def edit_player(id):
  player = Player.query.get_or_404(id)
  if (player.team == None or player.team.user_id != current_identity.id) and not current_identity.role.administrator:
    return forbidden('cannot edit this player')

  json_player = request.json
  if 'team_id' in json_player:
    if not current_identity.role.administrator:
      return forbidden('cannot change player\'s team')

    team = Team.query.get(json_player['team_id'])
    if team == None:
      return conflict('team doesn\'t exist')
    player.team_id = json_player['team_id']

  if 'value' in json_player:
    if not current_identity.role.administrator:
      return forbidden('cannot update player\'s value')
    player.value = json_player['value']

  if 'age' in json_player:
    if not current_identity.role.administrator:
      return forbidden('cannot update player\'s age')
    player.age = json_player['age']

  if 'price' in json_player:
    if not current_identity.role.administrator:
      return forbidden('cannot update player\'s price')
    player.price = json_player['price']

  if 'offer' in json_player:
    if not current_identity.role.administrator:
      return forbidden('cannot offer player')
    player.offer = json_player['offer']

  if 'name' in json_player:
    player.name = json_player['name']

  if 'lastname' in json_player:
    player.lastname = json_player['lastname']

  if 'country' in json_player:
    player.country = json_player['country']

  if 'position' in json_player:
    player.position = json_player['position']

  db.session.add(player)
  db.session.commit()

  return jsonify(player.to_json())


@api.route('/players/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_player(id):
  player = Player.query.get_or_404(id)
  db.session.delete(player)
  db.session.commit()
  return '', 204


@api.route('/players/market')
@jwt_required()
def get_players_market():
  query = Player.query.filter_by(offer=True)

  if request.args.get('team'):
    query = query.join(Team).filter(Team.name == request.args.get('team'))

  if request.args.get('country'):
    query = query.filter(Player.country == request.args.get('country'))

  if request.args.get('name'):
    query = query.filter(Player.name.ilike('%%%s%%' % request.args.get(
        'name')) | Player.lastname.ilike('%%%s%%' % request.args.get('name')))

  if request.args.get('minPrice'):
    query = query.filter(Player.price >= request.args.get('minPrice'))

  if request.args.get('maxPrice'):
    query = query.filter(Player.price <= request.args.get('maxPrice'))

  players = query.all()
  players = list(map(lambda p: p.to_json(show_price=True), players))
  return jsonify(players)


@api.route('/players/<int:id>/offer', methods=['POST'])
@jwt_required()
@validate_input(json_schema={
    'type': 'object',
    'properties': {
        'price': {
            'type': 'number',
            'minimum': 0
        }
    },
    'required': ['price']
})
def offer_player(id):
  player = Player.query.get_or_404(id)
  if player.team == None or player.team.user_id != current_identity.id:
    return forbidden('cannot edit this player')
  player.offer = True

  price = request.json['price']
  if price > 2*player.value:
    return bad_request('player\'s price cannot be more that 100% of current value')

  player.price = price

  return '', 204


@api.route('/players/<int:id>/cancel-offer', methods=['POST'])
@jwt_required()
def cancel_offer_player(id):
  player = Player.query.get_or_404(id)
  if player.team == None or player.team.user_id != current_identity.id:
    return forbidden('cannot edit this player')
  player.offer = False

  return '', 204


@api.route('/players/<int:id>/buy', methods=['POST'])
@jwt_required()
def buy_player(id):
  player = Player.query.get_or_404(id)
  if not player.offer:
    return bad_request('player is not in market')

  if player.team and player.team.user_id == current_identity.id:
    return bad_request('this player is already yours')

  team_dest = current_identity.team
  if not team_dest:
    return bad_request('you don\'t own a team')

  if player.price > team_dest.wallet:
    return bad_request('you don\'t have enough money to buy this player')

  team_orig = player.team
  if team_orig:
    team_orig.wallet += player.price
    db.session.add(team_orig)
  team_dest.wallet -= player.price
  player.team = team_dest
  player.value = update_player_price(player.value)
  player.offer = False

  db.session.add(player)
  db.session.commit()

  return '', 204
