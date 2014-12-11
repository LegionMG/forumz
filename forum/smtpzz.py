
SMTPserver = 'smtp.mail.ru'
sender =     'new_sitos@mail.ru'

USERNAME = "new_sitos"
PASSWORD = "123456q"

# typical values for text_subtype are plain, html, xml
text_subtype = 'plain'


content="""\
Test message
"""

subject="Sent from Python"

import sys
import os
import re

from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
# from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)
from email.mime.text import MIMEText
def sendpls(addr, link):
    try:
        print(link)
        msg = MIMEText(content+link, text_subtype)
        msg['Subject']=       subject
        msg['From']   = sender # some SMTP servers will do this automatically, not all

        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(sender, addr, msg.as_string())
            print(addr, msg.as_string())
        finally:
            conn.close()
    except Exception as e:
        print(e)