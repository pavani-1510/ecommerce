"""
Main Flask Application Entry Point
Simple, standard Flask setup - run with: python main.py
"""
import os
from pathlib import Path


# ============================================================================
# Environment Configuration
# ============================================================================

def _load_env_file(filename: str) -> None:
    """Load simple KEY=VALUE pairs from local env files if present."""
    env_path = Path(__file__).resolve().parent / filename
    if not env_path.exists():
        return
    
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# Load environment files
_load_env_file('.env.local')
_load_env_file('.env')


# ============================================================================
# Flask App Creation and Startup
# ============================================================================

from config import get_config
from app import create_app

# Create Flask app
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run development server
    port = int(os.environ.get('PORT', 5000))
    flask_env = os.environ.get('FLASK_ENV', 'development')
    debug = flask_env == 'development'
    
    print(f"🚀 Starting Flask server")
    print(f"   Environment: {flask_env}")
    print(f"   URL: http://localhost:{port}")
    print(f"   Debug: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
