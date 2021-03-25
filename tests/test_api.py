import json

from flask import url_for

from abstract_test_api import AbstractAPITestCase


class APITestCase(AbstractAPITestCase):
  def test_404(self):
    response = self.client.get('/wrong/url')
    self.assertTrue(response.status_code == 404)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'not found')

  def test_405(self):
    response = self.client.post(url_for('api.get_roles'))
    self.assertTrue(response.status_code == 405)
    json_response = json.loads(response.data.decode('utf-8'))
    self.assertTrue(json_response['error'] == 'method not allowed')
