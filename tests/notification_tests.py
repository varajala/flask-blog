import subprocess as subp
import tempfile
import pathlib
import sys
import base64

import microtest
import microtest.utils as utils

from contextlib import suppress
from threading import Lock

import flask_blog.notifications as notifications


LOCALHOST = '127.0.0.1'
SMTP_PORT = 25000
EMAIL_ADDR = 'test@email.com'
EMAIL_PASSWORD = 'password'


class CredentialFile:
    def __init__(self):
        self.count = 0

    def readline(self):
        if self.count == 0:
            self.count = 1
            return EMAIL_ADDR
        
        self.count = 0
        return EMAIL_PASSWORD

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def open_credential_file(*args, **kwargs):
    return CredentialFile()


@microtest.setup
def setup():
    global file, proc
    proc = utils.start_smtp_server(port=SMTP_PORT)


@microtest.cleanup
def cleanup():
    proc.terminate()


@microtest.test
def test_loading_credentials():
    try:
        cred_file = tempfile.TemporaryFile(mode='w+')
        cred_file.write('email-addr\npassword')
        cred_file.seek(0)

        email, password = notifications.load_credentials(cred_file.fileno())
        assert email == 'email-addr'
        assert password == 'password'

    finally:
        with suppress(OSError):
            cred_file.close()


@microtest.test
def test_sending_email(): 
    message = {
        'content': ('<p>message</p>', 'html'),
        'subject':'testing'
    }
    recv = 'recv@mail.com'
    server_addr = '127.0.0.1'

    builtins = notifications.__builtins__.copy()
    builtins['open'] = open_credential_file

    mutex = Lock()
    notifications.mutex = mutex

    with microtest.patch(notifications, __builtins__ = builtins):
        notifications.send_email(
            message,
            recv,
            (LOCALHOST, SMTP_PORT),
            'credentials',
            use_ssl = False
            )

    with mutex:
        email = proc.read_output()
        assert f'To: {recv}' in email
        assert f'From: {EMAIL_ADDR}' in email
        assert 'Subject: testing' in email
        assert base64.b64encode(b'<p>message</p>').decode() in email
