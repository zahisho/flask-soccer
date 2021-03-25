from functools import wraps

from flask import request
from flask_jwt import current_identity
from jsonschema import FormatChecker, ValidationError, validate

from .errors import bad_request, forbidden


def admin_required():
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      if not current_identity.role.administrator:
        return forbidden('insufficient permissions')
      return f(*args, **kwargs)
    return decorated_function
  return decorator


def validate_input(json_schema):
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      try:
        if not request.is_json:
          return bad_request('only JSON content allowed')
        validate(request.json, schema=json_schema,
                 format_checker=FormatChecker())
      except ValidationError as e:
        return bad_request(e.message)
      return f(*args, **kwargs)
    return decorated_function
  return decorator
