import os
import pytest
import app as museum_app

@pytest.fixture(scope='module')
def client():
    museum_app.app.config['TESTING'] = True
    with museum_app.app.test_client() as c:
        yield c

def test_login_page_loads(client):
    r = client.get('/login')
    assert r.status_code == 200
    assert b'Art Museum Login' in r.data

def test_register_csrf_present(client):
    r = client.get('/register')
    assert b'csrf_token' in r.data

def test_username_available_endpoint_blank(client):
    r = client.get('/api/username_available?u=')
    assert r.json['available'] is False

# NOTE: Additional tests for successful registration/login would require
# an isolated test database or cleanup steps to avoid mutating production data.
