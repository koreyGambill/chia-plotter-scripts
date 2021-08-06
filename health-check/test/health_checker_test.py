import sys, os
from unittest import mock
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Adding src packages path
from src.health_checker import health_checker
import requests
import smtplib
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import pytest
from freezegun import freeze_time

###################################
# Setup Mocks
###################################

class MockResponse:
    def __init__(self, result, message):
        self.result = result
        self.message = message

    def json(self):
        return {
            "result": self.result,
            "message": self.message
        }

    def self(self, *args, **kwargs):
        return self

class MockedSMTP:
    def __init__(self, smtp_location, *args, **kwargs):
        print('Initialize connection to %s with args %s and kwargs %s' % (smtp_location, str(args), str(kwargs.keys())))

    def __enter__(self):
        print('Mocked enter function')
        return self

    def login(self, email, password):
        print('logged into %s with a super secret password!' % email)

    def send_message(self, email_message):
        pass  # This will be mocked (to be watched), so no point in declaring it

    def __exit__(self, *args):
        print('Mocked exit function')
        self.close()
    
    def close(self):
        print('this is where it would close the connection')

class MockConfig:
    def __init__(self, smtp_location):
        self.smtp_location = smtp_location

    def mocked_get_config(self):
        return {
            "health_checker_config": {
                "notification_email": "some.user@gmail.com",
                "from_email": "HealthCheckBot@chia-health-checker.dev",
                "server": "127.0.0.1",
                "smtp_location": self.smtp_location
            },
            "shared_config": {
                "port": 5566
            }
        }

class MockData:
    def __init__(self, last_notification_time, last_notification_status):
        self.last_notification_time = str(last_notification_time)
        self.last_notification_status = last_notification_status

    def mocked_get_last_notification_data(self):
        return {
            "last_notification_time": self.last_notification_time,
            "last_notification_status": self.last_notification_status
        }

def mocked_write_current_notification_data(*args):
    pass

def setup_tests(monkeypatch, mock_server_response, mock_data, mock_config):
    monkeypatch.setattr(requests, "get", mock_server_response.self)
    monkeypatch.setattr(smtplib, "SMTP", MockedSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockedSMTP)
    monkeypatch.setattr(health_checker, "write_current_notification_data", mocked_write_current_notification_data)
    monkeypatch.setattr(health_checker, 'get_config', mock_config.mocked_get_config)
    monkeypatch.setattr(health_checker, "get_last_notification_data", mock_data.mocked_get_last_notification_data)
    MockedSMTP.send_message = MagicMock()

###################################
# Start Tests
###################################

def test_status_switched(monkeypatch):
    mock_server_response = MockResponse("unhealthy", "Service has been down for 999 seconds")
    last_notification_time = datetime.now() - timedelta(minutes=30)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="healthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)

    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

def test_message_sent_healthy_unhealthy_switch_gmail(monkeypatch):
    mock_server_response = MockResponse("healthy", "Service checked plots 99 seconds ago")
    mock_data = MockData(last_notification_time="2021-08-04 16:20:42.972704", last_notification_status="unhealthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)

    os.environ["gmail_app_password"] = "abcd1234"
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

###################################
# The rest have status NOT switched
###################################

def test_healthy_in_morning_window_no_recent_notification(monkeypatch):
    mock_server_response = MockResponse("healthy", "Service checked plots 99 seconds ago")
    some_morning_time = datetime(2021, 8, 5, 7, 35, 12, 123)
    last_notification_time = some_morning_time - timedelta(minutes=90)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="healthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    with freeze_time(str(some_morning_time)):
        health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

def test_healthy_in_morning_window_with_recent_notification(monkeypatch):
    mock_server_response = MockResponse("healthy", "Service checked plots 99 seconds ago")
    some_morning_time = datetime(2021, 8, 5, 7, 35, 12, 123)
    last_notification_time = some_morning_time - timedelta(minutes=20)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="healthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    with freeze_time(str(some_morning_time)):
        health_checker.health_check()
    MockedSMTP.send_message.assert_not_called()

def test_healthy_no_recent_notification(monkeypatch):
    mock_server_response = MockResponse("healthy", "Service checked plots 99 seconds ago")
    last_notification_time = datetime.now() - timedelta(hours=12)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="healthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

def test_healthy_with_recent_notification(monkeypatch):
    mock_server_response = MockResponse("healthy", "Service checked plots 99 seconds ago")
    last_notification_time = datetime.now() - timedelta(hours=11)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="healthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    health_checker.health_check()
    MockedSMTP.send_message.assert_not_called()

def test_unhealthy_no_recent_notification(monkeypatch):
    mock_server_response = MockResponse("unhealthy", "Service has been down for 999 seconds")
    last_notification_time = datetime.now() - timedelta(minutes=60)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="unhealthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

def test_unhealthy_with_recent_notification(monkeypatch):
    mock_server_response = MockResponse("unhealthy", "Did not find an eligible farming log in the last X entries")
    last_notification_time = datetime.now() - timedelta(minutes=59)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="unhealthy")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    health_checker.health_check()
    MockedSMTP.send_message.assert_not_called()

def test_unknown_no_recent_notification(monkeypatch):
    mock_server_response = MockResponse("unknown", "Health check server caught exception")
    last_notification_time = datetime.now() - timedelta(minutes=700)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="unknown")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

def test_unknown_with_recent_notification(monkeypatch):
    mock_server_response = MockResponse("unknown", "Some other exception message")
    last_notification_time = datetime.now() - timedelta(minutes=40)
    mock_data = MockData(last_notification_time=last_notification_time, last_notification_status="unknown")
    mock_config = MockConfig(smtp_location='local')
    setup_tests(monkeypatch, mock_server_response, mock_data, mock_config)
    health_checker.health_check()
    MockedSMTP.send_message.assert_not_called()

# Used for debugging
if __name__ == "__main__":
    pytest.main([os.path.realpath(__file__), "--log-cli-level=DEBUG", "-s"])