from flask import url_for

from .. import db


class Player(db.Model):
  __tablename__ = 'players'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), nullable=False)
  lastname = db.Column(db.String(64), nullable=False)
  country = db.Column(db.String(64), nullable=False)
  team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
  team = db.relationship('Team', backref=db.backref(
      'players', lazy=True))
  value = db.Column(db.Integer, nullable=False)
  age = db.Column(db.Integer, nullable=False)
  offer = db.Column(db.Boolean, default=False)
  price = db.Column(db.Integer)
  position = db.Column(db.String(64), nullable=False)

  def to_json(self, show_price=False):
    json_player = {
        'id': self.id,
        'url': url_for('api.get_player', id=self.id, _external=True),
        'name': self.name,
        'lastname': self.lastname,
        'country': self.country,
        'value': self.value,
        'age': self.age,
        'position': self.position
    }
    if self.team_id:
      json_player['team'] = url_for(
          'api.get_team', id=self.team_id, _external=True)
    if show_price:
      json_player['price'] = self.price
    return json_player
