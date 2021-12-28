# flask-blog
Simple Flask blog website extended from the Flask tutorial app.
Includes csrf protection, server side sessions, account verification via email and admin roles...


## Install and Setup

Clone the repository and navigate into the toplevel directory.
First, create a virtual environment:

    python -m venv venv


Next, install dependencies:

    ./venv/bin/python -m pip install -r requirements.txt


Install the actual application package:

    ./venv/bin/python -m pip install --editable .


Here you can run the test suite with:

    ./venv/bin/python -m microtest tests


Set up the flask environment:

    export FLASK_APP=flask_blog
    export FLASK_ENV=development


Initialize the database:

    flask init-db


Optionally create an admin user:

    flask create-admin


Run the app on locahost:5000:

    flask run --port 5000


By default the app will print all emails to the console, to actually send emails,
provide the SMTP host info in the flask_blog.config-module and create a file for your email
credentials. This file must be in the following format: **emailaddress\npassword**
