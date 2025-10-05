# run.py
import uvicorn
from app.main import app
from app.config import settings

if __name__ == "__main__":
    # Railway sets PORT automatically — use it!
    port = int(settings.PORT)  # This reads from env var PORT
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )