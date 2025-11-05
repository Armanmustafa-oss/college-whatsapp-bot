#!/usr/bin/env python3
"""
🔧 Enterprise Database Setup Script
===================================
Initializes the Supabase database with the enterprise schema.
Applies migrations and optionally seeds the database with sample data.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import subprocess
from supabase import create_client, Client as SupabaseClient

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SCHEMA_FILE_PATH = Path(os.getenv("SCHEMA_FILE_PATH", "./database/migrations/v2_enterprise_schema.sql"))
SEED_FILE_PATH = Path(os.getenv("SEED_FILE_PATH", "./database/seeds/sample_conversations.sql")) # Optional
USE_PSQL = os.getenv("USE_PSQL", "false").lower() == "true" # Fallback to psql if Supabase client fails for DDL

def _get_supabase_client():
    """Creates and returns a Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Connected to Supabase for setup.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Supabase using client library: {e}")
        if USE_PSQL:
            logger.info("Attempting to use psql command-line tool as fallback.")
            return None # Indicate to use psql
        else:
            logger.error("PSQL fallback not enabled. Setup cannot proceed without a client.")
            raise e

def _apply_schema_psql(schema_file: Path):
    """Applies the schema using the psql command-line tool."""
    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}")
        return False

    # Use the connection string (URL) with psql
    # psql "postgresql://postgres:[key]@[host]:[port]/[db]" -f schema_file.sql
    # Supabase URL is usually in the format postgresql://[user]:[password]@[host]:[port]/[database]
    # We can pass the full URL directly to psql
    conn_str = SUPABASE_URL
    if not conn_str.startswith("postgresql://"):
        logger.error("SUPABASE_URL must be a full PostgreSQL connection string for psql.")
        return False

    cmd = ["psql", "-d", conn_str, "-f", str(schema_file)]
    logger.info(f"Applying schema using psql: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Schema applied successfully via psql.")
        logger.debug(f"psql output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"psql command failed: {e.stderr}")
        return False

def _apply_schema_client(supabase_client: SupabaseClient, schema_file: Path):
    """Applies the schema using the Supabase client (execute raw SQL)."""
    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}")
        return False

    try:
        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Supabase client doesn't have a direct method to execute arbitrary DDL like schema creation
        # in the same way a raw psql connection might. The `table()` methods are for DML on existing tables.
        # For DDL (Data Definition Language - CREATE, ALTER, DROP), psql is often preferred or required.
        # However, if the schema consists only of INSERT/UPDATE/DELETE on existing tables (unlikely for initial setup),
        # the client could be used.
        # For initial schema setup (CREATE TABLE, etc.), psql is the standard tool.
        # This function is kept for potential future client library features or specific use cases.
        # For now, it's primarily illustrative.
        logger.warning("Executing DDL (CREATE TABLE, etc.) via Supabase client is not standard. Using psql is recommended.")
        # Example of DML (not DDL) with client:
        # supabase_client.table("some_table").insert({"key": "value"}).execute()
        # DDL execution might require a raw connection or psql.
        # Returning False to indicate this method is not suitable for schema creation.
        return False
    except Exception as e:
        logger.error(f"Failed to apply schema using client: {e}")
        return False

def _apply_seed_data(supabase_client: SupabaseClient, seed_file: Path):
    """Applies seed data using the Supabase client (execute raw SQL)."""
    if not seed_file.exists():
        logger.info(f"Seed file not found or not specified: {seed_file}. Skipping seeding.")
        return True # Not an error, just skipped

    try:
        with open(seed_file, 'r') as f:
            seed_sql = f.read()

        # Similar to schema, executing raw SQL for seeding might be easier with psql,
        # but for DML (INSERT, UPDATE) within existing tables, the client *might* work if it supports raw SQL execution.
        # Supabase client is primarily for interacting with tables via table().select/insert/update/delete.
        # For complex seed scripts with multiple statements, psql is often preferred.
        # However, for simple inserts, we can try using the client's table methods.
        # Example for sample_conversations.sql content:
        # INSERT INTO conversations ...; INSERT INTO conversations ...;
        # This requires parsing the SQL file, which is complex.
        # Using psql for seed data is often simpler.
        # Let's assume the seed file contains standard INSERT statements.
        # We will use psql for seeding as well for consistency and simplicity.
        logger.info(f"Applying seed data using psql from file: {seed_file}")
        conn_str = SUPABASE_URL
        cmd = ["psql", "-d", conn_str, "-f", str(seed_file)]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Seed data applied successfully via psql.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"psql command for seeding failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to apply seed data: {e}")
        return False

def setup_database():
    """Main setup function."""
    logger.info("Starting database setup process...")

    supabase_client = _get_supabase_client()

    success = False
    if supabase_client is None:
        # Use psql
        success = _apply_schema_psql(SCHEMA_FILE_PATH)
    else:
        # Attempt to use client (likely to fail for DDL)
        success = _apply_schema_client(supabase_client, SCHEMA_FILE_PATH)
        if not success:
            logger.info("Client method failed for schema, attempting psql fallback.")
            success = _apply_schema_psql(SCHEMA_FILE_PATH)

    if not success:
        logger.critical("Database schema application failed.")
        sys.exit(1)

    # Apply seed data (using psql)
    seed_success = _apply_seed_data(supabase_client, SEED_FILE_PATH) # Pass client (unused) for consistency
    if not seed_success:
        logger.warning("Database seed data application failed. Check the seed file and connection.")

    logger.info("Database setup process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Supabase database with enterprise schema.")
    # parser.add_argument("--schema-file", type=Path, help="Path to the schema SQL file (default: env var SCHEMA_FILE_PATH)")
    # parser.add_argument("--seed-file", type=Path, help="Path to the seed SQL file (default: env var SEED_FILE_PATH)")

    args = parser.parse_args()

    # Override env vars if arguments provided (optional)
    # if args.schema_file:
    #     SCHEMA_FILE_PATH = args.schema_file
    # if args.seed_file is not None: # Allow explicit None
    #     SEED_FILE_PATH = args.seed_file

    try:
        setup_database()
    except Exception as e:
        logger.critical(f"Database setup failed: {e}")
        sys.exit(1)