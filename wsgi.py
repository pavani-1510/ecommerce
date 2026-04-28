"""
WSGI Entry Point
"""
import os
from dotenv import load_dotenv

# Load environment variables, preferring local development settings
load_dotenv('.env.local', override=True)
load_dotenv('.env', override=False)

from app import create_app

# Create Flask app
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run()
