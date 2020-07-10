import configparser
import requests
import os
import logging
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import VSA


#Dev var
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
logging.getLogger().setLevel(logging.DEBUG)


# Init config
config = configparser.ConfigParser()
config.read('VSA_API.ini')
try:
    client_id = config['VSA']['client_id']
    client_secret = config['VSA']['client_secret']
    vsa_uri = config['VSA']['vsa_uri']

    redirect_uri = config['Listener']['redirect_uri']
    listen_port = config['Listener']['listen_port']

    #email_uri = config['Email'].getboolean('email_uri')
    smtp_username = config['Email']['smtp_username']
    smtp_password = config['Email']['smtp_password']
    smtp_emailfrom = config['Email']['smtp_emailfrom']
    smtp_emailto = config['Email']['smtp_emailto']
    smtp_server = config['Email']['smtp_server']
    smtp_port = int(config['Email']['smtp_port'])
    alerts_email = config['Email']['alerts_email']
except(KeyError):
    print("A required variable is missing. RIPERONI. ")
    exit()

authendpoint = vsa_uri + "/api/v1.0/authorize"

urlforuser = vsa_uri + "/vsapres/web20/core/login.aspx?response_type=code&redirect_uri=" + redirect_uri + "&client_id=" + client_id


def doInitialAuth(body):
    print("ImportListener found someone authing!")
    # Get first refresh token
    #code = body.split("?code=")[1]
    code = body
    r = requests.post(authendpoint, json={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret})
    print("First refresh token:")
    print(r.text)
    if(r.status_code == 400):
        print("An error has occurred")
        print(r.text)
        exit()
    refreshtoken = r.json()['refresh_token']
    print("Got token:")
    print(refreshtoken)
    print("Response code:")
    print(str(r.status_code))
    config['Auth'] = r.json()
    config['Auth']['refreshed_at'] = datetime.datetime.now().strftime("%Y%m%d%H%M")
    with open('VSA_API.ini', 'w') as configfile:
        config.write(configfile)
    VSA.Auth.doRefresh(refreshtoken)


class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.end_headers()

    def _html(self, message):
        # Blank response ( Aussie bandwidth is valuable! )
        # TODO: Test removal of these content statements, or change to None
        content = f""
        return content.encode("utf8")

    def do_GET(self):
        print("Do_GET!")
        self._set_headers()

        #match = re.match(r"\/code\?(.*)", self.path)
        #if(match):
        print("Auth attempt!\n")
        #QUERY_STRING = match.group(1)
        # We have the query string here.
        doInitialAuth(self.path)

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()

    
if __name__ == "__main__":
    print("Attempting initial auth")
    print("Please visit this link and copy the ?code part of the URL that results after you log in.")
    print("Ensure you include the code part (paste here ?code=xxxxxxxxxxxxxxxxxxx)\n")
    print(urlforuser)

    msg = MIMEMultipart('mixed')
    msg['Subject'] = "VSAPY Authentication"
    msg['From'] = smtp_emailfrom
    msg['To'] = smtp_emailto
    message = MIMEText('Please follow this link to authenticate your new integration: ' + urlforuser)
    msg.attach(message)
    code = input("Paste code here: ")
    doInitialAuth(code)


#    smtp_server = smtplib.SMTP(smtp_server, smtp_port)
#    smtp_server.ehlo()
   # smtp_server.starttls()
  #  smtp_server.ehlo()
 #   smtp_server.login(smtp_username, smtp_password)
#    smtp_server.sendmail(smtp_emailfrom, smtp_emailto, msg.as_string())
#    smtp_server.close()

    server_class = HTTPServer
    handler_class = S
    port = int(config['Listener']['listen_port'])
    addr = config['Listener']['listen_ip']
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
    print(f"Watching on {addr}:{port} for the auth response.\n")
#    httpd.handle_request()

    print("Request handled.")

    #WaitForAuth()
    #doRefresh()
    pass

