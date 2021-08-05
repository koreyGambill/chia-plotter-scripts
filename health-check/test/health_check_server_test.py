import sys, os.path, json
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Adding src packages path
from src.health_check_server import app
import pytest

healthy_message = {"result": "healthy", "message": "Service checked plots 2 seconds ago"}

# TODO: Add example log output files, and load them in instead to perform multiple tests
# This will also force me to break up the app.py into smaller functions so I can mock them
def test_health_check():
    response_raw = app.health_check()
    response = json.loads(response_raw[0])
    assert response['result'] in ['healthy', 'unhealthy', 'unknown']
    assert len(response['message']) != 0

# Used for debugging
if __name__ == "__main__":
    pytest.main([os.path.realpath(__file__), "--log-cli-level=DEBUG", "-s"])