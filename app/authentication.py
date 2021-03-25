
def authenticate(username, password):
  from .models import User
  user = User.query.filter_by(email=username).first()
  if user and user.verify_password(password):
    return user


def identity(payload):
  from .models import User
  user_id = payload['identity']
  return User.query.get(user_id)
