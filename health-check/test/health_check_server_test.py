import sys, os.path, json
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Adding src packages path
from src.health_check_server import app
from datetime import datetime
import pytest

healthy_message = {"result": "healthy", "message": "Service checked plots 2 seconds ago"}

# def test_health_check_healthy(monkeypatch):
#     healthy_log_file = os.path.join(os.path.dirname(__file__), 'healthy-chia-log.log')
#     older_healthy_datetime = datetime.strptime('2021-08-05T18:02:19.723', '%Y-%m-%dT%H:%M:%S.%f')
#     monkeypatch.setattr(app, 'chia_logs_file', healthy_log_file)
#     # TODO: Fix this override
#     monkeypatch.setattr(datetime, 'now', older_healthy_datetime)
#     response_raw = app.health_check()
#     response = json.loads(response_raw[0])
#     assert response['result'] == 'healthy'
#     assert 'Service checked plots' in response['message']

def test_health_check_unhealthy_because_old(monkeypatch):
    old_healthy_log_file = os.path.join(os.path.dirname(__file__), 'healthy-chia-log.log')
    monkeypatch.setattr(app, 'chia_logs_file', old_healthy_log_file)
    response_raw = app.health_check()
    response = json.loads(response_raw[0])
    assert response['result'] == 'unhealthy'
    assert 'Service has been down for' in response['message']

def test_health_check_unhealthy_because_no_logs_found(monkeypatch):
    unhealthy_log_file = os.path.join(os.path.dirname(__file__), 'unhealthy-chia-log.log')
    monkeypatch.setattr(app, 'chia_logs_file', unhealthy_log_file)
    response_raw = app.health_check()
    response = json.loads(response_raw[0])
    assert response['result'] == 'unhealthy'
    assert 'Did not find an eligible farming log in the last' in response['message']

# def test_health_check_exception(monkeypatch):
#     # TODO: Make app.process_response_from_log() throw an exception
#     response_raw = app.health_check()
#     response = json.loads(response_raw[0])
#     assert response['result'] == 'unknown'
#     assert 'Health check server caught exception' in response['message']

# Used for debugging
if __name__ == "__main__":
    pytest.main([os.path.realpath(__file__), "--log-cli-level=DEBUG", "-s"])