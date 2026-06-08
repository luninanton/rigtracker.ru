import sys
import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Insert the virtualenv site-packages path to resolve dependencies on the host
sys.path.insert(1, os.path.join(BASE_DIR, ".venv/lib/python3.11/site-packages"))
sys.path.insert(1, os.path.join(BASE_DIR, ".venv/lib/python3.12/site-packages"))

from a2wsgi import ASGIMiddleware
from backend.app.main import app

application = ASGIMiddleware(app)
