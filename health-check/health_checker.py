import logging
import os
import requests
import smtplib
import json
from pathlib import Path
from datetime import datetime, time, timedelta
from email.message import EmailMessage

# Set up logging
file_path = os.path.dirname(__file__)
health_checker_log_file = os.path.join(file_path, "logs/health-checker.log")
if not os.path.exists(health_checker_log_file):
    Path(health_checker_log_file).parent.mkdir(parents=True, exist_ok=True)
    open(health_checker_log_file, 'w').close
logging.basicConfig(filename=health_checker_log_file, level=logging.DEBUG, format=f'%(asctime)s %(levelname)s: %(message)s')

# Read out config
health_check_config_file = os.path.join(file_path, "config/health-check-config.json")
if not os.path.exists(health_check_config_file):
    logging.error("health-check-config.json file is not configured.")
    raise FileNotFoundError("health-check-config.json file is not configured. "
        "Set it up according to the steps in the README.md")
with open(health_check_config_file) as config:
    config_json = json.load(config)
NOTIFICATION_EMAIL = config_json['notification_email']
FROM_EMAIL = config_json['from_email']
SERVER_IP = config_json['server_ip']
PORT = config_json['port']

# Read out last notification data
data_file = os.path.join(file_path, "data/health-checker-db.json")
if not os.path.exists(data_file):
    Path(data_file).parent.mkdir(parents=True, exist_ok=True)
    with open(data_file, 'w') as data:
        # Write the initial data
        data.write(json.dumps({
            "last_notification_time": str(datetime.now() - timedelta(hours=24)),
            "last_notification_status": str("unknown")
            }))

def should_send_email(content):
    # Read in data
    with open(data_file) as data:
        last_notification_data = json.load(data)
    last_notification_status = last_notification_data["last_notification_status"]
    last_notification_time = datetime.strptime(last_notification_data["last_notification_time"], '%Y-%m-%d %H:%M:%S.%f')

    current_notification_status = content["result"]
    current_notification_time = datetime.now()

    should_send_email = False

    # If status ever changes, notify. This includes unhealthy -> unknown or visa versa.
    if last_notification_status != current_notification_status:
        logging.debug("Status Changed! Sending notification email")
        should_send_email = True

    # If last and current status are healthy only notify every 24 hours.
    elif (current_notification_status == "healthy" 
      and (current_notification_time - timedelta(hours=24)) > last_notification_time
      and time(7,0,0) < datetime.now().time() < time(8,0,0)):
        logging.debug("Status is still healthy, but it's been 24 hours so sending notification email")
        should_send_email = True

    # If status is not healthy then notify every 1 hour
    elif (current_notification_status != "healthy"
      and (current_notification_time - timedelta(hours=1)) > last_notification_time):
        logging.debug("Status is still not healthy, but it's been 1 hour so sending notification email")
        should_send_email = True

    if should_send_email:
        with open(data_file, 'w') as data:
            data.write(json.dumps({
                "last_notification_time": str(current_notification_time),
                "last_notification_status": current_notification_status
                }))
        return True

    logging.debug("Not sending email because the status did not change from {status} "
        "and the last notification was too recent: {time}".format(status=current_notification_status, time=last_notification_time))
    return False

def send_email(content):
    msg = EmailMessage()
    msg.set_content("Health check returned: %s" % content)
    msg['Subject'] = "Chia Health Status: %s" % content["result"]
    msg['FROM'] = FROM_EMAIL
    msg['TO'] = NOTIFICATION_EMAIL

    logging.info("sending email: %s" % msg)

    smtp_obj = smtplib.SMTP('localhost')
    smtp_obj.send_message(msg)

def main():
    health_check_url = 'http://%s:%d/health-check' % (SERVER_IP, PORT)
    logging.debug("requesting health check to %s" % health_check_url)
    try:
        r = requests.get(health_check_url, timeout=1)
        content = r.json()
        logging.debug("Request came back: %s" % content)
        if should_send_email(content):
            send_email(content)
    except requests.exceptions.RequestException as e:
        logging.warning("Error when requesting health check: %s" % e)
        message = {
            "result": "unknown",
            "message": str(e)
        }
        if should_send_email(message):
            send_email(message)

if __name__ == "__main__":
    main()