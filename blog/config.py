import sys
from pathlib import Path


filepath = Path(__file__)

EMAIL_HOST = (None, sys.stdout)
#EMAIL_HOST = ('smtp.gmail.com', 465),
EMAIL_USE_SSL = True
EMAIL_CREDENTIALS = '/home/varajala/dev/mail'

DATABASE = str(filepath.parent.joinpath('database.db'))

SECRET_KEY = 'dev'