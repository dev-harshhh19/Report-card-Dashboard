import os
import sys
import importlib.util
from pathlib import Path

# Set production environment explicitly if not set
os.environ.setdefault('FLASK_ENV', 'production')

# Load the main application module despite the hyphen in the filename
file_path = Path(__file__).parent / 'Report-card-Dashboard.py'
spec = importlib.util.spec_from_file_location("main_app", file_path)
main_app = importlib.util.module_from_spec(spec)
sys.modules["main_app"] = main_app
spec.loader.exec_module(main_app)

# Export the application object for WSGI servers
app = main_app.app

if __name__ == "__main__":
    app.run()
