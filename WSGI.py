# File Name: WSGI.py

# Description: WSGI to run on pythonanywhere.com
#######################
import sys

# project directory to the sys.path
project_home = u'/home/worles/Repos/covid19_dash'

if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# need to pass the app as "application" WSGI to work
from Dashboard import app
application = app.server
