import os
import tempfile
import pytest
import base64
import json
from flask import request, jsonify

os.environ['APP_SETTINGS'] = "testing"

from SSAPI import app, db, guard
from SSAPI.models import User


def decode_jwt(jwt):
    decoded_jwt = base64.b64decode(jwt.split('.')[1] + '===')
    return json.loads(decoded_jwt)


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(User(
            username='admin',
            password=guard.encrypt_password('admin'),
            firstname='administrator',
            lastname='administrator',
            roles='admin,presenter,advisor',
        ))

        db.session.add(User(
            username='presenter',
            password=guard.encrypt_password('presenter'),
            firstname='presenter',
            lastname='presenter',
            roles='presenter',
        ))

        db.session.add(User(
            username='advisor',
            password=guard.encrypt_password('advisor'),
            firstname='advisor',
            lastname='advisor',
            roles='advisor',
        ))

        db.session.commit()

    yield client
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


# -----------------------------
# User Management Tests
# -----------------------------
def login_client_helper(client, username, password):
    rv = client.post('/login', json={'username': username,
                                     'password': password})

    json_data = rv.get_json()
    return {'Authorization': 'Bearer ' + json_data['access_token']}


def test_client(client):
    rv = client.get('/')
    assert '200 OK' in rv.status


def test_login(client):
    rv = client.post('/login', json={'username': 'admin',
                                     'password': 'admin'})

    json_data = rv.get_json()
    token_data = decode_jwt(json_data['access_token'])

    assert '200 OK' in rv.status
    assert token_data['id'] == 1
    assert 'admin' in token_data['rls']


def test_bad_username(client):
    rv = client.post('/login', json={'username': 'bogususer',
                                     'password': 'admin'})

    assert '401 UNAUTH' in rv.status


def test_bad_password(client):
    rv = client.post('/login', json={'username': 'admin',
                                     'password': 'badpass'})

    assert '401 UNAUTH' in rv.status


def test_create_user_noauth(client):
    rv = client.post('/Users', json={'username': 'newuser',
                                     'password': 'newpass',
                                     'firstname': 'Bob',
                                     'lastname': 'NewUser',
                                     'roles': 'presenter'})

    assert '200 OK' in rv.status

    json_data = rv.get_json()
    assert json_data['id'] > 0
    assert json_data['username'] == 'newuser'


def test_create_existing_account(client):
    rv = client.post('/Users', json={'username': 'admin',
                                     'password': 'newpass',
                                     'firstname': 'Bob',
                                     'lastname': 'NewUser',
                                     'roles': 'admin'})

    assert '412 PRECONDITION FAILED' in rv.status


def test_create_admin_user(client):
    rv = client.post('/Users', json={'username': 'newuser',
                                     'password': 'newpass',
                                     'firstname': 'Bob',
                                     'lastname': 'NewUser',
                                     'roles': 'admin'})

    assert '412 PRECONDITION FAILED' in rv.status


def test_show_user_noauth(client):
    rv = client.get('/Users')
    data = rv.get_json()
    assert '401 UN' in rv.status
    assert 'MissingTokenHeader' in data['error']


def test_show_user_auth(client):
    token = login_client_helper(client, 'admin', 'admin')
    rv = client.get('/Users/1', headers=token)

    assert '200 OK' in rv.status

    data = rv.get_json()
    assert data['id'] == 1
    assert 'administrator' in data['firstname']
    assert 'administrator' in data['lastname']


def test_show_user_notadmin(client):
    token = login_client_helper(client, 'presenter', 'presenter')
    rv = client.get('/Users/1', headers=token)

    assert '200 OK' in rv.status

    data = rv.get_json()
    assert data['id'] == 1
    assert 'administrator' in data['firstname']
    assert 'administrator' in data['lastname']


def test_delete_another_user(client):
    token = login_client_helper(client, 'presenter', 'presenter')
    rv = client.delete('/Users/3', headers=token)

    assert '401' in rv.status


def test_delete_user_asadmin(client):
    token = login_client_helper(client, 'admin', 'admin')
    rv = client.delete('/Users/3', headers=token)

    assert '204' in rv.status


def test_delete_user_self(client):
    token = login_client_helper(client, 'presenter', 'presenter')
    rv = client.delete('/Users/2', headers=token)

    assert '204' in rv.status


def test_changing_user_username(client):
    token = login_client_helper(client, 'presenter', 'presenter')
    rv = client.post('/Users/2', json={"username": "newPresenter"},
                     headers=token)

    assert '200' in rv.status
    data = rv.get_json()
    assert 'newPresenter' in data['username']


def test_changing_user_username_existing(client):
    token = login_client_helper(client, 'presenter', 'presenter')
    rv = client.post('/Users/2', json={"username": "advisor"},
                     headers=token)

    assert '409' in rv.status
    data = rv.get_json()


def test_change_user_asadmin(client):
    token = login_client_helper(client, 'admin', 'admin')
    rv = client.post('/Users/2', json={"username": "different"},
                     headers=token)

    assert '200' in rv.status
    data = rv.get_json()
    assert 'different' in data['username']


def test_change_another_user(client):
    token = login_client_helper(client, 'presenter', 'presenter')
    rv = client.post('/Users/3', json={"username": "different"},
                     headers=token)

    assert '401' in rv.status


def test_change_password(client):
    token = login_client_helper(client, 'presenter', 'presenter')
    rv = client.post('/Users/2', json={"password": "newpass"},
                     headers=token)

    assert '200' in rv.status

    rv = client.post('/login', json={"username": "presenter",
                                     "password": "presenter"})

    assert '401' in rv.status

    rv = client.post('/login', json={"username": "presenter",
                                     "password": "newpass"})

    assert '200' in rv.status


# -----------------------------
# Scrimmage Endpoint Tests
# -----------------------------
def test_create_scrimmage(client):
    token = login_client_helper(client, 'presenter', 'presenter')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    data = rv.get_json()
    assert 'Test Scrimmage' in data['subject']
    assert '2019' in data['schedule']
    assert 'Demo' in data['scrimmage_type']
    assert data['max_advisors'] == 1
    assert not data['scrimmage_complete']
    assert 2 in data['presenters']


def test_create_scrimmage_noauth(client):
    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1})

    assert '401' in rv.status


def test_list_scrimmages(client):
    token = login_client_helper(client, 'presenter', 'presenter')

    # Create a Scrimmage
    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    rv = client.get('/Scrimmages', headers=token)
    data = rv.get_json()
    assert '200' in rv.status
    assert len(data) == 1


def test_list_scrimmages_all_noadmin(client):
    token = login_client_helper(client, 'presenter', 'presenter')

    # Create a Scrimmage
    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [1],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    rv = client.get('/Scrimmages', data={'all': True}, headers=token)

    data = rv.get_json()
    assert '200' in rv.status
    assert len(data) == 1


def test_list_scrimmages_advisor_only(client):
    token = login_client_helper(client, 'presenter', 'presenter')

    # Create a Scrimmage
    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    rv = client.get('/Scrimmages', data={'role': 'advisor'}, headers=token)
    data = rv.get_json()
    assert '200' in rv.status
    assert len(data) == 0


def test_create_scrimmage_no_max_advisor(client):
    token = login_client_helper(client, 'presenter', 'presenter')

    # Create a Scrimmage
    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2]},
                     headers=token)

    assert '200' in rv.status

    rv = client.get('/Scrimmages/1', headers=token)
    data = rv.get_json()
    assert '200' in rv.status
    assert data['max_advisors'] == 5


def test_list_scrimmages_presenter_only(client):
    token = login_client_helper(client, 'presenter', 'presenter')

    # Create a Scrimmage
    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [1],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    rv = client.get('/Scrimmages', data={'role': 'presenter'}, headers=token)
    data = rv.get_json()
    assert '200' in rv.status
    assert len(data) == 1


def test_list_all_scrimmages(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)

    assert '200' in rv.status

    rv = client.get('/Scrimmages', data={'all': True}, headers=token)
    assert '200' in rv.status

    data = rv.get_json()
    assert len(data) == 2


def test_set_scrimmage_complete(client):
    token = login_client_helper(client, 'admin', 'admin')
    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.post('/Scrimmages/1', json={'scrimmage_complete': True},
                     headers=token)

    assert '200' in rv.status


def test_list_all_scrimmages_completed(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.post('/Scrimmages/1', json={'scrimmage_complete': True},
                     headers=token)

    assert '200' in rv.status

    rv = client.get('/Scrimmages', data={'all': True,
                                         'scrimmage_complete': True},
                    headers=token)

    assert '200'in rv.status
    data = rv.get_json()
    assert len(data) == 1


def test_change_scrimmage_presenters(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.post('/Scrimmages/1', json={'presenters': [1, 2]},
                     headers=token)
    assert '200' in rv.status

    data = rv.get_json()
    assert "Test Scrimmage" in data['subject']
    assert '2019-04-23T18:25:43.511Z' in data['schedule']
    assert 'Demo' in data['scrimmage_type']
    assert 1 in data['presenters']
    assert 2 in data['presenters']
    assert data['max_advisors'] == 1


def test_change_scrimmage_multiple_items(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.post('/Scrimmages/1', json={'presenters': [1, 2],
                                            'scrimmage_type': 'Pitch'},
                     headers=token)
    assert '200' in rv.status

    data = rv.get_json()
    assert "Test Scrimmage" in data['subject']
    assert '2019-04-23T18:25:43.511Z' in data['schedule']
    assert 'Pitch' in data['scrimmage_type']
    assert 1 in data['presenters']
    assert 2 in data['presenters']
    assert data['max_advisors'] == 1


def test_get_specific_scrimmage(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.get('/Scrimmages/1', headers=token)
    assert '200' in rv.status

    data = rv.get_json()
    assert "Test Scrimmage" in data['subject']
    assert '2019-04-23T18:25:43.511Z' in data['schedule']
    assert 'Demo' in data['scrimmage_type']
    assert 2 in data['presenters']
    assert data['max_advisors'] == 1


def test_get_nonexisting_scrimmage(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.get('/Scrimmage/2', headers=token)

    assert '404' in rv.status


def test_delete_scrimmage_admin(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.delete('/Scrimmages/1', headers=token)
    assert '204' in rv.status


def test_scrimmage_add_advisor(client):
    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.post('/Scrimmages/1', json={'advisors': [3]},
                     headers=token)


def test_scrimmage_add_nonadvisor(client):

    token = login_client_helper(client, 'admin', 'admin')

    rv = client.post('/Scrimmages', json={'subject': "Test Scrimmage",
                                          'schedule': '2019-04-23T18:25:43.511Z',
                                          'scrimmage_type': 'Demo',
                                          'presenters': [2],
                                          'max_advisors': 1},
                     headers=token)
    assert '200' in rv.status

    rv = client.post('/Scrimmages/1', json={'advisors': [2]},
                     headers=token)

    assert '400' in rv.status


def test_scrimmage_add_toomany_advisors(client):
    pass