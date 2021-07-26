# Health Check Server
This server indicates whether the chia farmer is still successfully farming. This is meant to be hit by another service - like a gcp cloud function - that will do health checks periodically and send an email if it's been down for x amount of time.

## Setup Environment
Navigate to health-check in terminal and run the commands
``` bash
python3 -m venv ./health-check-env
source ./health-check-env/bin/activate
python3 -m pip install -r requirements.txt
deactivate
cp ./config/health-check-config-example.json ./config/health-check-config.json
```
Then update the health-check-config.json with your specific configuration and the IP address of your server. Acceptable values for smtp_location are 'local' or 'gmail'.

## Run Server
`bash path/to/health-check/run-server-dev.sh` - Starts the server

## Allow Traffic
`sudo ufw enable`  
`sudo ufw allow from <trusted_IP_address> to any port 5566`

## Example Request
`curl -i 127.0.0.1:5566/health-check`

## Example Responses

```
HTTP/1.0 200 OK
ContentType: application/json
Content-Type: text/html; charset=utf-8
Content-Length: 71
Server: Werkzeug/2.0.1 Python/3.8.10
Date: Thu, 22 Jul 2021 00:01:44 GMT

{"result": "healthy", "message": "Service checked plots 2 seconds ago"}%     
```

```
HTTP/1.0 200 OK
ContentType: application/json
Content-Type: text/html; charset=utf-8
Content-Length: 119
Server: Werkzeug/2.0.1 Python/3.8.10
Date: Thu, 22 Jul 2021 02:52:52 GMT

{"result": "unhealthy", "message": "Service has been down for 700 seconds."}%   
```

```
HTTP/1.0 200 OK
ContentType: application/json
Content-Type: text/html; charset=utf-8
Content-Length: 119
Server: Werkzeug/2.0.1 Python/3.8.10
Date: Thu, 22 Jul 2021 02:52:52 GMT

{"result": "unhealthy", "message": "Service has been down for 700 seconds."}%   
```

```
HTTP/1.0 500 INTERNAL SERVER ERROR
ContentType: application/json
Content-Type: text/html; charset=utf-8
Content-Length: 119
Server: Werkzeug/2.0.1 Python/3.8.10
Date: Thu, 22 Jul 2021 04:24:26 GMT

{"result": "unknown", "message": "Health check server caught exception <exception message>"}%   
```

```
HTTP/1.0 500 INTERNAL SERVER ERROR
Content-Type: text/html; charset=utf-8
Content-Length: 290
Server: Werkzeug/2.0.1 Python/3.8.10
Date: Thu, 22 Jul 2021 02:43:35 GMT

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>500 Internal Server Error</title>
<h1>Internal Server Error</h1>
<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
```

## Start Server Automatically
If you want to just run the server automatically whenever you start your computer, you can run it as a daemon using systemd (assuming you are on Linux). To do this, just add a file named "chia-health-check-server.service" to the folder /etc/systemd/system and populate it with the following text (replace \<user> with your user).

```
[Unit]
Description="Starts a Flask server that allows health checking a chia farmer by scraping chia logs"
After=network.target

[Service]
User=<user>
WorkingDirectory=/home/<user>/path/to/chia-plotter-scripts
ExecStart=bash ./health-check/run-server-dev.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Then just do a daemon-reload, and you can manage your server using systemctl.

Here are a few useful commands:

`sudo systemctl daemon-reload` - Load the new service file
`sudo systemctl enable chia-health-check-server` - Start server automatically upon startup  
`sudo systemctl start chia-health-check-server` - Start server immediately  
`sudo systemctl stop chia-health-check-server` - Stop server  
`sudo systemctl disable chia-health-check-server` - Disable running server on startup   
`sudo journalctl -u chia-health-check-server` - See systemd logs for service

## Check that your server is working
You should be able to run a command like `curl -i 127.0.0.1:5566/health-check` and get a response.

## Setup chia-health-checker
If the server is working, you are ready to set up a script to do the health checks. It's best if the health_checker script is ran on a different computer, and even better if on a different internet connection. GCP Cloud Functions would be an excellent way to ping the health-check-server.

## Local Setup
This would be a great use for a raspberry pi - which is what I will run this from.

### Setup Code
Navigate to health-check in terminal and run the commands

``` bash
python3 -m venv ./health-check-env
source ./health-check-env/bin/activate
python3 -m pip install -r requirements.txt
deactivate
cp ./config/health-check-config-example.json ./config/health-check-config.json
```

Then update the health-check-config.json with your specific configuration and the IP address of your server. Acceptable values for smtp_location are 'local' or 'gmail'. Then follow either the Setup Local SMTP Server or Setup Gmail instructions below depending on your choice.

### Option 1) Setup Local SMTP Server
The code is able to be ran with a local SMTP server or with a gmail account.

Here's a [great guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-as-a-send-only-smtp-server-on-ubuntu-18-04) from digital ocean on setting up an SMTP server which will allow you to send mail from your local machine.

[This one](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-on-ubuntu-20-04) is more current, but doesn't go through certbot setup.

### Option 2) Setup Gmail
It's a good idea to create a gmail account specifically for this application. Then in your settings you just need to enable 2 factor authentication and then create an App password - that's the password you'll use for this application and you'll need to save it in the chia-health-checker.service file. See the Setup Daemon section below.

### Test Before Daemon
If you are using a local SMTP server, you can just run the health_checker.py script in the virtual environment. 

If you are using a gmail server, you can run test-health-checker.sh to run the script after loading the password as an environment variable. First you'll need to create the file '$HOME/.apikey/chia-health-checker-gmail.pass' and paste your app password into it.

It's recommended to do a `chmod 600 $HOME/.apikey/chia-health-checker-gmail.pass` command as well to make sure your user is the only one with read/write. Note that anyone with root access on your computer will still have access to view it.

### Setup Daemon
If you're using systemd, you can create these two files to run this script on a timer:

/etc/systemd/system/chia-health-checker.timer
```
[Unit]
Description="timer for chia-health-checker"
Requires=chia-health-checker.service

[Timer]
Unit=chia-health-checker.service
OnCalendar=*:0/5

[Install]
WantedBy=timers.target
```

/etc/systemd/system/chia-health-checker.service
```
[Unit]
Description="Checks the status of chia farming, and emails user if unhealthy."
Wants=chia-health-checker.service

[Service]
Type=oneshot
Environment=gmail_app_password=<password>
ExecStart=/home/<user>/path/to/chia-plotter-scripts/health-check/health-check-env/bin/python3 /home/<user>/path/to/chia-plotter-scripts/health-check/health_checker.py

[Install]
WantedBy=multi-user.target
```

Replace the password on the Environment entry (or delete the line if you are using a local SMTP server), and replace the user and path on the ExecStart entry. Then you will need to run enable and start commands on both the service and the timer. See list of helpful systemctl commands above.


### Unblock Emails
If you set up a gmail to send emails through, they shouldn't be marked as spam.

If you set up a local SMTP server and did not purchase a domain and setup certificates, your emails will likely be going to your spam folder. On gmail it's really easy to set up a rule to let those into your inbox just by going into settings -> (tab) Filters and Blocked Addresses -> Create a new filter.

After unblocking the emails, you should be getting emails to your inbox instead of to spam.