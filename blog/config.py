import sys
import os


EMAIL_HOST = (None, sys.stdout)
# EMAIL_HOST = ('smtp.gmail.com', 465),
EMAIL_USE_SSL = True
EMAIL_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'email-credentials')

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

SECRET_KEY = 'development'


if not os.path.exists(EMAIL_CREDENTIALS):
    with open(EMAIL_CREDENTIALS, 'wb') as file:
        file.write(b'email-address')
        file.write(b'\n')
        file.write(b'password')
