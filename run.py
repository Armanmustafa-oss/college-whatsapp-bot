# run.py (project root)
import os
import sys

# Ensure project root is on sys.path so "app" package can be imported reliably
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Try to set up logging gracefully
try:
    try:
        from .utils.logger import setup_logging
        setup_logging()
    except ImportError:
        pass
except Exception as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).warning(f"setup_logging() failed or not available: {e}")

import uvicorn
from app.config import settings

def main():
    # Use uvicorn import-string so uvicorn imports the package correctly
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main()
