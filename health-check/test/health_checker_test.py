import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Adding src packages path
from src.health_checker import health_checker
import requests
import smtplib
from unittest.mock import MagicMock
from datetime import datetime
import pytest

# TODO: I would like to make the returned MockResponse dynamic based on the test. Can this be done with fixtures?
healthy_message = {"result": "healthy", "message": "Service checked plots 99 seconds ago"}

class MockResponse:
    @staticmethod
    def json():
        return healthy_message

def mock_response_get(*args, **kwargs):
        return MockResponse()

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

smtplib.SMTP=MockedSMTP

def mocked_get_config_local():
    return {
    "health_checker_config": {
        "notification_email": "some.user@gmail.com",
        "from_email": "HealthCheckBot@chia-health-checker.dev",
        "server": "127.0.0.1",
        "smtp_location": "local"
    },
    "shared_config": {
        "port": 5566
    }
}

def mocked_get_config_gmail():
    return {
    "health_checker_config": {
        "notification_email": "some.user@gmail.com",
        "from_email": "HealthCheckBot@chia-health-checker.dev",
        "server": "127.0.0.1",
        "smtp_location": "gmail"
    },
    "shared_config": {
        "port": 5566
    }
}

def default_setup_local(monkeypatch):
    monkeypatch.setattr(requests, "get", mock_response_get)
    monkeypatch.setattr(smtplib, "SMTP", MockedSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockedSMTP)
    monkeypatch.setattr(health_checker, "get_config", mocked_get_config_local)
    MockedSMTP.send_message = MagicMock()

def default_setup_gmail(monkeypatch):
    monkeypatch.setattr(requests, "get", mock_response_get)
    monkeypatch.setattr(smtplib, "SMTP", MockedSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockedSMTP)
    monkeypatch.setattr(health_checker, "get_config", mocked_get_config_gmail)
    MockedSMTP.send_message = MagicMock()

def test_no_message_sent_healthy_status_no_switch(monkeypatch):
    default_setup_local(monkeypatch)
    # TODO: Can I make this function a fixture to make it more dynamic?
    def mocked_get_last_notification_data():
        return {
            "last_notification_time": str(datetime.now()),
            "last_notification_status": "healthy"
        }
    monkeypatch.setattr(health_checker, "get_last_notification_data", mocked_get_last_notification_data)
    health_checker.health_check()
    MockedSMTP.send_message.assert_not_called()

def test_message_sent_unhealthy_status_switch_local(monkeypatch):
    default_setup_local(monkeypatch)
    def mocked_get_last_notification_data():
        return {
            "last_notification_time": "2021-08-04 16:20:42.972704",
            "last_notification_status": "unhealthy"
        }
    monkeypatch.setattr(health_checker, "get_last_notification_data", mocked_get_last_notification_data)
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

def test_message_sent_unhealthy_status_switch_gmail(monkeypatch):
    default_setup_gmail(monkeypatch)
    def mocked_get_last_notification_data():
        return {
            "last_notification_time": "2021-08-04 16:20:42.972704",
            "last_notification_status": "unhealthy"
        }
    monkeypatch.setattr(health_checker, "get_last_notification_data", mocked_get_last_notification_data)
    os.environ["gmail_app_password"] = "abcd1234"
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

# Used for debugging
if __name__ == "__main__":
    pytest.main([os.path.realpath(__file__), "--log-cli-level=DEBUG", "-s"])