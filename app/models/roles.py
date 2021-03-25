from flask import url_for

from .. import db


class Role(db.Model):
  __tablename__ = 'roles'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), unique=True)
  users = db.relationship('User', backref='role', lazy='dynamic')
  administrator = db.Column(db.Boolean, default=False)
  default = db.Column(db.Boolean, default=False)

  @staticmethod
  def create_roles():
    role_admin = Role(name='Administrator', administrator=True)
    role_user = Role(name='User', default=True)

    db.session.add(role_admin)
    db.session.add(role_user)
    db.session.commit()

  def to_json(self):
    json_role = {
        'url': url_for('api.get_role', id=self.id, _external=True),
        'name': self.name,
        'id': self.id
    }
    return json_role
