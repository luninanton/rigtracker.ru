import sys
import os
import glob

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Dynamically add virtualenv site-packages paths for any Python 3.x version
site_packages_pattern = os.path.join(BASE_DIR, ".venv/lib/python3.*/site-packages")
for path in glob.glob(site_packages_pattern):
    sys.path.insert(1, path)

from a2wsgi import ASGIMiddleware
from backend.app.main import app

application = ASGIMiddleware(app)
