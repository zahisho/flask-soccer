from flask import jsonify, request, url_for
from flask_jwt import current_identity, jwt_required

from .. import db
from ..models import Team, User
from . import api
from .decorators import admin_required, validate_input
from .errors import conflict, forbidden


@api.route('/teams')
@jwt_required()
def get_teams():
  teams = Team.query.all()
  teams = list(map(lambda t: t.to_json(), teams))
  return jsonify(teams)


@api.route('/teams/<int:id>')
@jwt_required()
def get_team(id):
  team = Team.query.get_or_404(id)
  return jsonify(team.to_json())


@api.route('/teams', methods=['POST'])
@jwt_required()
@admin_required()
@validate_input(json_schema={
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string'
        },
        'country': {
            'type': 'string'
        },
        'wallet': {
            'type': 'number',
            'minimum': 0
        },
        'user_id': {
            'type': 'number'
        }
    },
    'required': ['name', 'country', 'wallet']
})
def new_team():
  json_team = request.json
  team = Team(
      name=json_team['name'], country=json_team['country'], wallet=json_team['wallet'])
  if 'user_id' in json_team:
    user = User.query.get(json_team['user_id'])
    if user == None:
      return conflict('user doesn\'t exist')
    elif user.team:
      return conflict('user already has a team')
    team.user_id = json_team['user_id']
  db.session.add(team)
  db.session.commit()

  return jsonify(team.to_json()), 201, {'Location': url_for('api.get_team', id=team.id, _external=True)}


@api.route('/teams/<int:id>', methods=['PUT'])
@jwt_required()
@validate_input(json_schema={
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string'
        },
        'country': {
            'type': 'string'
        },
        'wallet': {
            'type': 'number',
            'minimum': 0
        },
        'user_id': {
            'type': 'number'
        }
    }
})
def edit_team(id):
  team = Team.query.get_or_404(id)
  if team.user_id != current_identity.id and not current_identity.role.administrator:
    return forbidden('cannot edit this team')

  json_team = request.json
  if 'user_id' in json_team:
    if not current_identity.role.administrator:
      return forbidden('cannot change team\'s owner')

    user = User.query.get(json_team['user_id'])
    if user == None:
      return conflict('user doesn\'t exist')
    elif user.team:
      return conflict('user already has a team')
    team.user_id = json_team['user_id']

  if 'wallet' in json_team:
    if not current_identity.role.administrator:
      return forbidden('cannot update team\'s wallet')
    team.wallet = json_team['wallet']

  if 'name' in json_team:
    team.name = json_team['name']

  if 'country' in json_team:
    team.country = json_team['country']

  db.session.add(team)
  db.session.commit()

  return jsonify(team.to_json())


@api.route('/teams/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_team(id):
  team = Team.query.get_or_404(id)
  db.session.delete(team)
  db.session.commit()
  return '', 204


@api.route('/teams/<int:id>/players')
@jwt_required()
def get_team_players(id):
  team = Team.query.get_or_404(id)
  players = list(map(lambda p: p.to_json(), team.players))
  return jsonify(players)
