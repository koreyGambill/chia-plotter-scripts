import sys, os
from unittest import mock
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Adding src packages path
from src.health_checker import health_checker
import requests
import smtplib
from unittest.mock import MagicMock
from datetime import datetime
import pytest

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

class config:
    def __init__(self, last_notification_time, last_notification_status, smtp_location):
        self.last_notification_time = str(last_notification_time)
        self.last_notification_status = last_notification_status
        self.smtp_location = smtp_location

    def mocked_get_last_notification_data(self):
        return {
            "last_notification_time": self.last_notification_time,
            "last_notification_status": self.last_notification_status
        }

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

def write_current_notification_data(*args):
    pass

def setupXXX(monkeypatch, conf):
    mock_response = MockResponse("healthy", "Service checked plots 99 seconds ago")
    monkeypatch.setattr(requests, "get", mock_response.self)
    monkeypatch.setattr(smtplib, "SMTP", MockedSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockedSMTP)
    monkeypatch.setattr(health_checker, "write_current_notification_data", write_current_notification_data)
    monkeypatch.setattr(health_checker, 'get_config', conf.mocked_get_config)
    monkeypatch.setattr(health_checker, "get_last_notification_data", conf.mocked_get_last_notification_data)
    MockedSMTP.send_message = MagicMock()

def test_no_message_sent_healthy_status_no_switch(monkeypatch):
    conf = config(last_notification_time="2021-08-05 16:20:42.972704", last_notification_status="healthy", smtp_location='local')
    setupXXX(monkeypatch, conf)
    health_checker.health_check()
    MockedSMTP.send_message.assert_not_called()

def test_message_sent_unhealthy_status_switch_local(monkeypatch):
    conf = config(last_notification_time="2021-08-04 16:20:42.972704", last_notification_status="unhealthy", smtp_location='local')
    setupXXX(monkeypatch, conf)
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

def test_message_sent_unhealthy_status_switch_gmail(monkeypatch):
    conf = config(last_notification_time="2021-08-04 16:20:42.972704", last_notification_status="unhealthy", smtp_location='gmail')
    setupXXX(monkeypatch, conf)
    os.environ["gmail_app_password"] = "abcd1234"
    health_checker.health_check()
    MockedSMTP.send_message.assert_called_once()

# Used for debugging
if __name__ == "__main__":
    pytest.main([os.path.realpath(__file__), "--log-cli-level=DEBUG", "-s"])