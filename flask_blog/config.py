import sys
import os


# For testing
EMAIL_HOST = (None, sys.stdout)

# For actually sending emails
# EMAIL_HOST = ('smtp.gmail.com', 465)

EMAIL_USE_SSL = True
EMAIL_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'email-credentials')

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

SECRET_KEY = 'development'
