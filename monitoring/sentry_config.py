"""
🚨 Enterprise-Grade Error Tracking & Observability Core
=======================================================
Centralized Sentry configuration and management layer.
Provides context-aware error capture, performance monitoring,
and custom metric collection for proactive issue resolution.
"""

import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from typing import Optional, Dict, Any
import traceback
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SentryManager:
    """
    Singleton-like manager for initializing, configuring, and interacting
    with the Sentry SDK throughout the application lifecycle.
    Ensures consistent tagging, context attachment, and custom event capture.
    Relies on the *global* sentry_sdk state initialized elsewhere (e.g., bot/main.py).
    """
    _initialized = False
    _environment = None

    @classmethod
    def initialize(
        cls,
        environment: str, # Pass the environment string directly
        traces_sample_rate: float = 1.0,
        profiles_sample_rate: float = 1.0, # Enable profiling for performance insights
        release: Optional[str] = None,
        server_name: Optional[str] = None
    ):
        """
        Initializes the Sentry SDK with enterprise-grade settings.
        This method should typically be called *once* during application startup,
        ideally *after* the main `sentry_sdk.init()` call in the main application file (bot/main.py)
        to ensure global state is already set up, or it can be the *primary* initialization point.
        """
        if cls._initialized:
            logger.warning("SentryManager already initialized. Skipping re-initialization.")
            return

        # Store environment for potential use in methods that need it directly
        cls._environment = environment

        # Note: This method assumes sentry_sdk.init was called externally (e.g., in bot/main.py)
        # or this is the primary place to call it.
        # If this is the *only* place, ensure DSN is available here, perhaps by passing it too,
        # or by reading it again from config within this method.
        # For now, assuming bot/main.py handles the main init().

        # Example: If this WAS the main init point:
        # import os # Or import from bot.config
        # dsn = os.getenv("SENTRY_DSN") # Or BOT_CONFIG.SENTRY_DSN
        # if dsn:
        #     sentry_sdk.init(
        #         dsn=dsn,
        #         environment=environment,
        #         traces_sample_rate=traces_sample_rate,
        #         profiles_sample_rate=profiles_sample_rate,
        #         release=release,
        #         server_name=server_name,
        #         # ... other options
        #     )
        #     cls._initialized = True
        # else:
        #     logger.warning("SENTRY_DSN not found, skipping Sentry initialization.")
        #     return

        # Since bot/main.py calls sentry_sdk.init, we just confirm and set up our manager state.
        # Check if sentry_sdk is initialized by checking its hub's client
        # This is a basic check, sentry_sdk might have other ways to confirm initialization status.
        if sentry_sdk.Hub.current.client is not None:
             cls._initialized = True
             logger.info(f"✅ SentryManager linked to global Sentry SDK for environment: {environment}")
        else:
             logger.warning("⚠️ SentryManager: Global Sentry SDK does not appear to be initialized. Manager functions may not work.")


    @staticmethod
    def capture_exception_with_context(
        exception: Exception,
        extra_context: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Captures an exception with rich, contextual information.
        Relies on the global sentry_sdk state.
        """
        if not SentryManager._initialized:
            logger.error("SentryManager not initialized. Cannot capture exception.")
            return

        with sentry_sdk.configure_scope() as scope:
            if extra_context:
                scope.set_extra("context", extra_context)
            if user_context:
                scope.set_user(user_context)
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)

        logger.error(f"Capturing exception to Sentry: {exception}", exc_info=True)
        sentry_sdk.capture_exception(exception)

    @classmethod
    @contextmanager
    def start_transaction(cls, name: str, op: str = "default"):
        """
        Context manager to start a Sentry performance transaction.
        Relies on the global sentry_sdk state.
        """
        if not cls._initialized:
            logger.warning("SentryManager not initialized. Transaction context manager is a no-op.")
            yield
            return

        with sentry_sdk.start_transaction(name=name, op=op) as transaction:
            logger.debug(f"Started Sentry transaction: {name}")
            yield transaction
            logger.debug(f"Finished Sentry transaction: {name}")

    @staticmethod
    def add_breadcrumb(
        message: str,
        category: str = "custom",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Adds a custom breadcrumb to the current Sentry scope (global state).
        """
        if not SentryManager._initialized:
            # Even if not initialized, log the breadcrumb attempt for debugging
            logger.debug(f"Sentry not initialized. Breadcrumb would have been: {message}")
            return

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data
        )
        logger.debug(f"Added breadcrumb: {message}")

    @staticmethod
    def set_user_context(user_data: Dict[str, Any]):
        """
        Sets user context for the current Sentry scope (global state).
        """
        if not SentryManager._initialized:
            logger.warning("SentryManager not initialized. Cannot set user context.")
            return

        sentry_sdk.set_user(user_data)
        logger.debug(f"Set Sentry user context: {user_data.get('id', 'unknown')}")

    @staticmethod
    def set_tag(key: str, value: str):
        """
        Sets a custom tag for the current Sentry scope (global state).
        """
        if not SentryManager._initialized:
            logger.warning("SentryManager not initialized. Cannot set tag.")
            return

        sentry_sdk.set_tag(key, value)
        logger.debug(f"Set Sentry tag: {key}={value}")

    @staticmethod
    def set_extra(key: str, value: Any):
        """
        Sets custom extra data for the current Sentry scope (global state).
        """
        if not SentryManager._initialized:
            logger.warning("SentryManager not initialized. Cannot set extra data.")
            return

        sentry_sdk.set_extra(key, value)
        logger.debug(f"Set Sentry extra data: {key}")


# Example usage (if run as main):
# if __name__ == "__main__":
#     # Example initialization (requires a real DSN)
#     # SentryManager.initialize(
#     #     environment="development",
#     #     traces_sample_rate=1.0
#     # )
#     # Example of capturing an exception with context
#     # try:
#     #     raise ValueError("An example error")
#     # except ValueError as e:
#     #     SentryManager.capture_exception_with_context(
#     #         e,
#     #         extra_context={"user_query": "What are fees?", "session_id": "abc123"},
#     #         user_context={"id": "user456", "ip_address": "192.168.1.1"},
#     #         tags={"intent": "fees", "error_type": "context_missing"}
#     #     )