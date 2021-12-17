import sys
import os


# For testing / development (print messages into console)
EMAIL_HOST = (None, sys.stdout)

# For actually sending emails, change this into a tuple
# in format: (host address: str, host_port: int).
# For exaple for using gmail:
# EMAIL_HOST = ('smtp.gmail.com', 465)

EMAIL_USE_SSL = True

# A file with format: "emailaddress\npassword"
EMAIL_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'email-credentials')

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

SECRET_KEY = 'development'
