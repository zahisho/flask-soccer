import traceback

from flask import jsonify
from werkzeug.exceptions import BadRequest

from . import api


@api.app_errorhandler(400)
def bad_request(description):
  if type(description) == BadRequest:
    description = description.description
  response = jsonify({'error': 'bad request', 'description': description})
  response.status_code = 400
  return response


def forbidden(description):
  response = jsonify({'error': 'forbidden', 'description': description})
  response.status_code = 403
  return response


@api.app_errorhandler(404)
def page_not_found(e):
  response = jsonify({'error': 'not found'})
  response.status_code = 404
  return response


@api.app_errorhandler(405)
def method_not_allowed(e):
  response = jsonify({'error': 'method not allowed'})
  response.status_code = 405
  return response


def conflict(description):
  response = jsonify({'error': 'conflict', 'description': description})
  response.status_code = 409
  return response


@api.app_errorhandler(500)
@api.app_errorhandler(Exception)
def internal_server_error(e):
  traceback.print_exc()
  response = jsonify({'error': 'internal server error'})
  response.status_code = 500
  return response
