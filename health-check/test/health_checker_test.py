import pytest, sys, os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Adding src packages path
from src.health_checker import health_checker
import requests
import smtplib

healthy_message = {"result": "healthy", "message": "Service checked plots 9992 seconds ago"}

class MockResponse:
    @staticmethod
    def json():
        return healthy_message

def mock_response_get(*args, **kwargs):
        return MockResponse()

class MockedSMTP(object):
    def __init__(self, object):
        print('Initialize connection with object %s' % str(object))

    def login(self, email, password):
        print('logged into %s with a super secret password!' % email)

    def send_message(self, email_message):
        print('sending message %s' % email_message)

    def quit(self):
        print('closed resources')

smtplib.SMTP=MockedSMTP

def test_main(monkeypatch):
    monkeypatch.setattr(requests, "get", mock_response_get)
    monkeypatch.setattr(smtplib, "SMTP", MockedSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockedSMTP)

    health_checker.HealthChecker().health_check()


# TODO: Create tests with fake data files so I can test the various conditions of should_send_email

# Used for debugging
if __name__ == "__main__":
    test_main(pytest.MonkeyPatch)