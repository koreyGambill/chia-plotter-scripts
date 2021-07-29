import logging
import os
import requests
import smtplib
import ssl
import json
from pathlib import Path
from datetime import datetime, time, timedelta
from email.message import EmailMessage

class HealthChecker:

    def __init__(self):
        file_path = os.path.dirname(__file__)
        self.root_path = os.path.join(file_path, '../..')
        self.health_checker_log_file = os.path.join(self.root_path, "logs/health-checker.log")
        self.health_check_config_file = os.path.join(self.root_path, "conf/health-check-config.json")
        self.data_file = os.path.join(self.root_path, "data/health-checker-db.json")

    def setup_logging(self):
        if not os.path.exists(self.health_checker_log_file):
            Path(self.health_checker_log_file).parent.mkdir(parents=True, exist_ok=True)
            open(self.health_checker_log_file, 'w').close
        logging.basicConfig(filename=self.health_checker_log_file, level=logging.DEBUG, format=f'%(asctime)s %(levelname)s: %(message)s')

    def get_config(self):
        if not os.path.exists(self.health_check_config_file):
            logging.error("health-check-config.json file is not configured.")
            raise FileNotFoundError("health-check-config.json file is not configured. "
                "Set it up according to the steps in the README.md")
        with open(self.health_check_config_file) as config:
            config_json = json.load(config)
        self.NOTIFICATION_EMAIL = config_json['health_checker_config']['notification_email']
        self.FROM_EMAIL = config_json['health_checker_config']['from_email']
        self.SERVER = config_json['health_checker_config']['server']
        self.SMTP_LOCATION = config_json['health_checker_config']['smtp_location']
        self.PORT = config_json['shared_config']['port']

    def get_last_notification_data(self):
        if not os.path.exists(self.data_file):
            Path(self.data_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, 'w') as data:
                # Write the initial data
                data.write(json.dumps({
                    "last_notification_time": str(datetime.now() - timedelta(hours=24)),
                    "last_notification_status": str("unknown")
                    }))
        with open(self.data_file) as data:
            last_notification_data = json.load(data)
        return last_notification_data

    def write_current_notification_data(self, current_notification_time, current_notification_status):
        with open(self.data_file, 'w') as data:
            data.write(json.dumps({
                "last_notification_time": str(current_notification_time),
                "last_notification_status": current_notification_status
                }))
        return True

    def should_send_email(self, content):
        last_notification_data = self.get_last_notification_data()
        last_notification_status = last_notification_data["last_notification_status"]
        last_notification_time = datetime.strptime(last_notification_data["last_notification_time"], '%Y-%m-%d %H:%M:%S.%f')
        
        current_notification_status = content["result"]
        current_notification_time = datetime.now()

        should_send_email = False

        # If status ever changes, notify. This includes unhealthy -> unknown or visa versa.
        if last_notification_status != current_notification_status:
            logging.debug("Status changed from %s to %s. Sending notification email" % (last_notification_status, current_notification_status))
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
            self.write_current_notification_data(current_notification_time, current_notification_status)

        logging.debug("Not sending email because the status did not change from {status} "
            "and the last notification was too recent: {time}".format(status=current_notification_status, time=last_notification_time))
        return False

    def send_email(self, content):
        msg = EmailMessage()
        msg.set_content("Health check returned: %s" % content)
        msg['Subject'] = "Chia Health Status: %s" % content["result"]
        msg['FROM'] = self.FROM_EMAIL
        msg['TO'] = self.NOTIFICATION_EMAIL

        logging.info("sending email: %s" % msg)

        if self.SMTP_LOCATION == 'local':
            with smtplib.SMTP('localhost') as server:
                server.send_message(msg)
        elif self.SMTP_LOCATION == 'gmail':
            gmail_app_password = os.getenv("gmail_app_password")
            if gmail_app_password != None:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
                    server.login(self.FROM_EMAIL, gmail_app_password)
                    server.send_message(msg)
            else:
                logging.warning("Could not send email through gmail. gmail_app_password not set in environment variables.")
        else:
            logging.warning("SMTP_LOCATION is not set to an accepted value.")


    def health_check(self):
        self.setup_logging()
        self.get_config()

        health_check_url = 'http://%s:%d/health-check' % (self.SERVER, self.PORT)
        logging.debug("requesting health check to %s" % health_check_url)
        try:
            r = requests.get(health_check_url, timeout=1)
            content = r.json()
            logging.debug("Request came back: %s" % content)
            if self.should_send_email(content):
                self.send_email(content)
        except requests.exceptions.RequestException as e:
            logging.warning("Error when requesting health check: %s" % e)
            message = {
                "result": "unknown",
                "message": str(e)
            }
            if self.should_send_email(message):
                self.send_email(message)

if __name__ == "__main__":
    HealthChecker().health_check()