from flask import url_for

from .. import db


class Team(db.Model):
  __tablename__ = 'teams'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), nullable=False)
  country = db.Column(db.String(64), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
  user = db.relationship('User', backref=db.backref(
      'team', lazy=True, uselist=False))
  wallet = db.Column(db.Integer, nullable=False)

  def to_json(self):
    json_team = {
        'id': self.id,
        'url': url_for('api.get_team', id=self.id, _external=True),
        'name': self.name,
        'country': self.country,
        'wallet': self.wallet,
        'players': url_for('api.get_team_players', id=self.id, _external=True)
    }
    if self.user_id:
      json_team['user'] = url_for(
          'api.get_user', id=self.user_id, _external=True)

    value = 0
    if self.players:
      for p in self.players:
        value += p.value

    json_team['value'] = value

    return json_team
