import os
import sys

# Ensure the root project directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Expose top-level variables expected by Vercel's Python runtime
application = app
handler = app
