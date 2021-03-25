from flask import url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db
from .roles import Role


class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(64), unique=True, index=True)
  role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)

  @property
  def password(self):
    raise AttributeError('password is not a readable attribute')

  @password.setter
  def password(self, password):
    self.password_hash = generate_password_hash(password)

  def verify_password(self, password):
    return check_password_hash(self.password_hash, password)

  def to_json(self):
    json_user = {
        'url': url_for('api.get_user', id=self.id, _external=True),
        'email': self.email,
        'id': self.id,
        'role': url_for('api.get_role', id=self.role_id, _external=True)
    }
    if self.team:
      json_user['team'] = url_for(
          'api.get_user_team', id=self.id, _external=True)
      json_user['players'] = url_for(
          'api.get_user_team_players', id=self.id, _external=True)
    return json_user

  @staticmethod
  def create_admin_user():
    user_admin = User(email='admin@admin.com', password='admin1234')
    role_admin = Role.query.filter_by(name='Administrator').first()

    user_admin.role_id = role_admin.id

    db.session.add(user_admin)
    db.session.commit()
