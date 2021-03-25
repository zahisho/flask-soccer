from flask import jsonify
from flask_jwt import jwt_required

from ..models import Role
from . import api


@api.route('/roles')
@jwt_required()
def get_roles():
  roles = Role.query.all()
  roles = list(map(lambda r: r.to_json(), roles))
  return jsonify(roles)


@api.route('/roles/<int:id>')
@jwt_required()
def get_role(id):
  role = Role.query.get_or_404(id)
  return jsonify(role.to_json())
