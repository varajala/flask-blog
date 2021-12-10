import flask
import smtplib
import ssl
import base64
import sys
import typing

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread


mutex = None


def load_credentials(credentials_file):
    with open(credentials_file) as file:
        email = file.readline().strip()
        password = file.readline().strip()
    return email, password


def write_email_to_stream(content, stream):
    meta, content = content.split('\n\n')
    stream.write(50 * '- ' + '\n')
    stream.write(meta)
    stream.write('\n\n')
    stream.write(base64.b64decode(content).decode('utf-8'))
    stream.write('\n')
    stream.write(50 * '- ' + '\n')


def send_email(message: dict, reciever: str, host: tuple, credentials_path: str, use_ssl=True):
    addr, port = host
    sender, password = load_credentials(credentials_path)

    content, content_type = message.get('content', ('', 'plain'))
    mime_msg = MIMEText(content, content_type, _charset='utf-8')
    mime_msg['Subject'] = message.get('subject', '')
    mime_msg['From'] = sender
    mime_msg['To'] = reciever

    reply_to = message.get('reply-to', sender)
    mime_msg.add_header('Reply-To', reply_to)

    if addr is None:
        write_email_to_stream(mime_msg.as_string(), port)
        return

    server: typing.Union[smtplib.SMTP_SSL, smtplib.SMTP]
    if use_ssl:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(addr, port, context=context)
    
    else:
        server = smtplib.SMTP(addr, port)

    def send():
        if mutex is not None:
            mutex.acquire()
        
        try:
            if use_ssl:
                server.login(sender, password)
            server.sendmail(sender, reciever, mime_msg.as_string())
        
        except smtplib.SMTPException as exc:
            sys.stderr.write(str(exc))

        finally:
            server.quit()
            if mutex is not None:
                mutex.release()
    
    Thread(target=send).start()
