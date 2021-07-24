from datetime import datetime
from flask import Flask
from pathlib import Path
import json
import logging
import re
import os

# Set up logging
file_path = os.path.dirname(__file__)
health_check_log_file = os.path.join(file_path, '../logs/health-check-server.log')
if not os.path.exists(health_check_log_file):
    Path(health_check_log_file).parent.mkdir(parents=True, exist_ok=True)
    open(health_check_log_file, 'w').close
logging.basicConfig(filename=health_check_log_file, level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# Read out config
health_check_config_file = os.path.join(file_path, '../config/health-check-config.json')
if not os.path.exists(health_check_config_file):
    logging.error("health-check-config.json file is not configured.")
    raise FileNotFoundError("health-check-config.json file is not configured. \n\
        Set it up according to the steps in the README.md")
with open(health_check_config_file) as config:
    config_json = json.load(config)
PORT = config_json["port"]
LINES_TO_SEARCH=100
CHIA_LOGS_FILE = os.path.join(Path.home(), '.chia/mainnet/log/debug.log')
DATETIME_REGEX = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}'

app = Flask(__name__)

def make_response(json_object, status=200):
    return (json.dumps(json_object), status, {'ContentType':'application/json'})

@app.route('/health-check')
def health_check():
    try:
        app.logger.info('\n***** Running health check *****')
        app.logger.debug('Checking for active chia logs')
        last_farming_log = None
        with open(CHIA_LOGS_FILE) as file:
            for line in (file.readlines() [-LINES_TO_SEARCH:]):
                if 'plots were eligible for farming' in line:
                    last_farming_log = line
        
        if last_farming_log == None:
            app.logger.warn('Did not find an eligible farming log in the last %d entries' % LINES_TO_SEARCH)
            return make_response({
                "result":"unhealthy",
                "message": "Did not find an eligible farming log in the last %d entries" % LINES_TO_SEARCH, 
            })

        app.logger.debug('Found last line: ' + last_farming_log)
        logs_time_match = re.search(DATETIME_REGEX, last_farming_log)
        
        if not logs_time_match:
            app.logger.warn('Could not parse a valid timestamp on ' + last_farming_log)
            return make_response({
                "result":"unhealthy",
                "message": "Could not parse a valid timestamp on %s" % last_farming_log,
            })

        logs_time_str = logs_time_match.group(0)
        datetime_logs = datetime.strptime(logs_time_str, '%Y-%m-%dT%H:%M:%S.%f')
        datetime_diff = (datetime.now() - datetime_logs).total_seconds()
        
        if datetime_diff > 600:
            return make_response({
                "result":"unhealthy",
                "message": "Service has been down for %d seconds." % datetime_diff,
            }) 
        else:
            app.logger.debug('Service checked plots %d seconds ago' % datetime_diff)
            return make_response({
                "result":"healthy",
                "message": "Service checked plots %d seconds ago" % datetime_diff
            })
    except Exception as e:
        # If I weren't sending this just to myself, I would send a more generic message and log the exception to look at later.
        # Because sending a "client" an error can be dangerous. However, I trust my email.
        return make_response({
            "result":"unknown",
            "message": "Health check server caught exception %s" % e
        }, 500)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=PORT)
