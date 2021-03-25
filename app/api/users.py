from flask import jsonify, request, url_for
from flask_jwt import current_identity, jwt_required

from .. import db
from ..models import Player, Role, Team, User
from ..utils import (get_random_age, get_random_country, get_random_firstname,
                     get_random_lastname)
from . import api
from .decorators import admin_required, validate_input
from .errors import conflict, forbidden, page_not_found


@api.route('/users')
@jwt_required()
def get_users():
  users = User.query.all()
  users = list(map(lambda u: u.to_json(), users))
  return jsonify(users)


@api.route('/users/<int:id>')
@jwt_required()
def get_user(id):
  user = User.query.get_or_404(id)
  return jsonify(user.to_json())


@api.route('/users', methods=['POST'])
@jwt_required()
@admin_required()
@validate_input(
    json_schema={
        'type': 'object',
        'properties': {
            'username': {
                'type': 'string',
                'format': 'email'
            },
            'password': {
                'type': 'string',
                'minLength': 8
            },
            'role_id': {
                'type': 'number'
            }
        },
        'required': ['username', 'password']
    }
)
def new_user():
  json_user = request.json
  user = User.query.filter_by(email=json_user['username']).first()
  if user:
    return conflict('email already registered')
  if 'role_id' not in json_user:
    role = Role.query.filter_by(default=True).first()
  else:
    role = Role.query.get(json_user['role_id'])
    if role == None:
      return conflict('role doesn\'t exist')
  user = User(email=json_user['username'],
              password=json_user['password'], role=role)
  db.session.add(user)
  db.session.commit()
  return jsonify(user.to_json()), 201,  {'Location': url_for('api.get_user', id=user.id, _external=True)}


@api.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
@validate_input(
    json_schema={
        'type': 'object',
        'properties': {
            'username': {
                'type': 'string',
                'format': 'email'
            },
            'password': {
                'type': 'string',
                'minLength': 8
            },
            'role_id': {
                'type': 'number'
            }
        }
    }
)
def edit_user(id):
  if id != current_identity.id and not current_identity.role.administrator:
    return forbidden('cannot edit other user')
  json_user = request.json

  if 'role_id' in json_user and not current_identity.role.administrator:
    return forbidden('cannot edit your role')

  user = User.query.get_or_404(id)

  if 'username' in json_user and json_user['username'] != user.email:
    if User.query.filter_by(email=json_user['username']).first():
      return conflict('email already registered')

    user.email = json_user['username']

  if 'password' in json_user:
    user.password = json_user['password']

  if 'role_id' in json_user:
    role = Role.query.get(json_user['role_id'])
    if role == None:
      return conflict('role doesn\'t exist')
    user.role = role

  db.session.add(user)
  db.session.commit()

  return jsonify(user.to_json())


@api.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(id):
  user = User.query.get_or_404(id)
  db.session.delete(user)
  db.session.commit()
  return '', 204


@api.route('/users/register', methods=['POST'])
@validate_input(
    json_schema={
        'type': 'object',
        'properties': {
            'username': {
                'type': 'string',
                'format': 'email'
            },
            'password': {
                'type': 'string',
                'minLength': 8
            }
        },
        'required': ['username', 'password']
    }
)
def register_user():
  json_user = request.json
  user = User.query.filter_by(email=json_user['username']).first()
  if user:
    return conflict('email already registered')
  role_user = Role.query.filter_by(name='User').first()
  user = User(email=json_user['username'],
              password=json_user['password'], role_id=role_user.id)

  # create user's team
  team = Team(name='New team', country=get_random_country(), wallet=5000000)
  team.user = user

  # create team's players
  alignment = [
      (3, 'Goalkeeper'),
      (6, 'Defender'),
      (6, 'Midfielder'),
      (5, 'Attacker')
  ]
  for qty, pos in alignment:
    for _ in range(qty):
      player = Player(name=get_random_firstname(), lastname=get_random_lastname(
      ), country=get_random_country(), value=1000000, age=get_random_age(), position=pos)
      team.players.append(player)
  db.session.add(user)
  db.session.add(team)
  db.session.commit()
  return jsonify(user.to_json()), 201,  {'Location': url_for('api.get_user', id=user.id, _external=True)}


@api.route('/users/<int:id>/team')
@jwt_required()
def get_user_team(id):
  user = User.query.get_or_404(id)
  if user.team:
    return jsonify(user.team.to_json())
  else:
    return page_not_found(None)


@api.route('/users/<int:id>/team/players')
@jwt_required()
def get_user_team_players(id):
  user = User.query.get_or_404(id)
  if user.team:
    players = [p.to_json() for p in user.team.players]
    return jsonify(players)
  else:
    return page_not_found(None)
