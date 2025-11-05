# Procfile for process management (used by platforms like Heroku, and potentially Railway)
# Defines the commands to run different processes of the application.

# The main bot service handling WhatsApp webhooks
web: uvicorn bot.main:app --host 0.0.0.0 --port $PORT

# Optional: The dashboard service (if running separately from the main bot)
# dashboard: uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT
# Note: If running the dashboard separately, you might need a different PORT or a fixed one like 8001,
# and Railway would need to be configured to expose multiple ports or route differently.
# For a single service exposing both, the 'web' process in railway.toml is sufficient,
# and the dashboard route is defined within the main FastAPI app (dashboard/app.py).