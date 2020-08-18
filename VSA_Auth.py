import configparser
import requests
import os
import logging
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import HTTPServer, BaseHTTPRequestHandler
from time import sleep
import re
from imaplib import IMAP4_SSL
import email
import VSA


#Dev var
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
logging.getLogger().setLevel(logging.DEBUG)


# Init config
config = configparser.ConfigParser()
fullpath = os.getcwd() + "\\PythonVSA\\config.ini"
config.read(fullpath, encoding='utf-8')
try:
    client_id = config['VSA']['client_id']
    client_secret = config['VSA']['client_secret']
    vsa_uri = config['VSA']['vsa_uri']

    redirect_uri = config['Listener']['redirect_uri']
    listen_port = config['Listener']['listen_port']

    smtp_username = config['Email']['smtp_username']
    smtp_password = config['Email']['smtp_password']
    smtp_emailfrom = config['Email']['smtp_emailfrom']
    smtp_emailto = config['Email']['smtp_emailto']
    smtp_server = config['Email']['smtp_server']
    smtp_port = int(config['Email']['smtp_port'])
    imap_username = config['Email']['imap_username']
    imap_password = config['Email']['imap_password']
    imap_email = config['Email']['imap_email']
    imap_server = config['Email']['imap_server']
    imap_port = int(config['Email']['imap_port'])
    imap_refresh_interval = int(config['Email']['imap_refresh_interval'])

except(KeyError):
    print("A required variable is missing. RIPERONI. ")
    exit()

authendpoint = vsa_uri + "/api/v1.0/authorize"

urlforuser = vsa_uri + "/vsapres/web20/core/login.aspx?response_type=code&redirect_uri=" + redirect_uri + "&client_id=" + client_id


def doInitialAuth(code):
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
    with open(fullpath, 'w') as configfile:
        config.write(configfile)
    VSA.Auth.doRefresh(refreshtoken)


if __name__ == "__main__":
    print("Attempting initial auth")
    print("Please visit this link and copy the entire resulting URL.")
    print(urlforuser)

    msg = MIMEMultipart('mixed')
    msg['Subject'] = "PythonVSA Authentication"
    msg['From'] = smtp_emailfrom
    msg['To'] = smtp_emailto
    text = f"""\
        Please follow this link to authenticate your new integration:  {urlforuser}

        Once you have authorized you will be redirected to a page that doesn't load/resolve. Copy the address from your address bar and reply to this email with it."""
    msg.attach(MIMEText(text))

    smtp_server = smtplib.SMTP(smtp_server, smtp_port)
    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.ehlo()
    smtp_server.login(smtp_username, smtp_password)
    smtp_server.sendmail(smtp_emailfrom, smtp_emailto, msg.as_string())
    smtp_server.close()

    print(f"Waiting {imap_refresh_interval} seconds to give a chance to respond.")
    sleep(imap_refresh_interval)

    connection = IMAP4_SSL(imap_server, imap_port)
    connection.login(imap_username, imap_password)
    typ, data = connection.select('INBOX')
    typ, data = connection.search(None, '(UNSEEN)')

    if(data == [b'']):
        print(f"No emails found. Checking again every {imap_refresh_interval} seconds.")
        i = 0
        while i < 5:
            i = i + 1
            print(f"Checking {5 - i} more times.")
            sleep(imap_refresh_interval)
            typ, data = connection.search(None, '(UNSEEN)')
            if(data[0] != b''):
                break

    for num in data[0].split():
        typ, data = connection.fetch(num, '(RFC822)')
        try:
            msg = email.message_from_bytes(data[1][1])
        except(IndexError):
            msg = email.message_from_bytes(data[0][1])

        typ, data = connection.store(num, '+FLAGS', '\\Seen')
        pattern = r'https://.*\/\?code(=[\w\d]{34})'
        pattern1 = r'https://.*\/\?code(=[\w\d]{32})'
        try:
            match = re.match(pattern, msg._payload)
            matchraw = re.match(pattern1, msg._payload)
        except(TypeError):
            print("It appears we have a message with a format we can't understand. Deleting.")
            continue
        if(match):
            code = match.group(1)
            code = code.replace("=3D", "")
            connection.close()
            connection.logout()
            doInitialAuth(code)
        elif(matchraw):
            connection.close()
            connection.logout()
            doInitialAuth(code)
        else:
            print("Didn't find URL. Deleting.")
    print("All done.")