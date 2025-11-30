# Use an official Python runtime as the base image
# Ensure this version matches PYTHON_VERSION in railway.toml or your requirements
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., git, build tools for some Python packages)
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# (Optional) Run the reindexing script during build if needed, or handle it at runtime
# RUN python scripts/reindex_documents.py

# Expose the port the app runs on (Railway provides $PORT)
# The command below will use $PORT

# Define the command to run the application
# This command should match what you had in START_CMD
# For the main bot service:
CMD ["sh", "-c", "python scripts/reindex_documents.py && python -m uvicorn bot.main:app --host 0.0.0.0 --port $PORT"]
# For the dashboard service (in a separate Dockerfile or different CMD):
# CMD ["sh", "-c", "python -m uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT"]
