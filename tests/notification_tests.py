import subprocess as subp
import tempfile
import pathlib
import sys
import socket
import time
import microtest
import base64
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


def wait_for_server_init():
    host = (LOCALHOST, SMTP_PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        while True:
            try:
                soc.connect(host)
            except OSError:
                time.sleep(0.01)
                continue
            else:
                break


def open_credential_file(*args, **kwargs):
    return CredentialFile()


@microtest.setup
def setup():
    global file, proc
    file = tempfile.TemporaryFile(mode='w+')

    script_path = pathlib.Path(__file__).parent.joinpath('smtp.sh')
    cmd = ['python3', '-u', '-m', 'smtpd', '-c', 'DebuggingServer', '-n', f'{LOCALHOST}:{SMTP_PORT}']
    proc = subp.Popen(cmd, stdout=file)
    wait_for_server_init()


@microtest.cleanup
def cleanup():
    try:
        proc.wait(0.5)
    except subp.TimeoutExpired:
        proc.kill()
    
    file.close()


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

    email_start = file.tell()
    
    with microtest.patch(notifications, __builtins__ = builtins):
        notifications.send_email(
            message,
            recv,
            (LOCALHOST, SMTP_PORT),
            'credentials',
            use_ssl = False
            )

    with mutex:
        file.seek(email_start)
        email = file.read()
        assert f'To: {recv}' in email
        assert f'From: {EMAIL_ADDR}' in email
        assert 'Subject: testing' in email
        assert base64.b64encode(b'<p>message</p>').decode() in email
