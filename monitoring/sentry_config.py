# monitoring/sentry_config.py

import logging
import sentry_sdk # Import sentry_sdk here
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
    Manager for interacting with Sentry SDK using its global state.
    Provides utility methods for capturing exceptions with context,
    managing breadcrumbs, users, tags, etc., relying on the global SDK initialized elsewhere.
    """
    _initialized = False
    _environment = None

    @classmethod
    def initialize(
        cls,
        environment: str, # Pass the environment string directly
        # Add other Sentry-specific config if needed, but avoid re-init
    ):
        """
        Performs any necessary one-time setup for the manager itself,
        *not* the SDK. The SDK should be initialized externally.
        """
        if cls._initialized:
             logger.warning("SentryManager already initialized. Skipping.")
             return

        cls._environment = environment
        cls._initialized = True
        logger.info(f"✅ SentryManager initialized for environment: {environment}")

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
        sentry_sdk.capture_exception(exception) # Use the global function

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

        with sentry_sdk.start_transaction(name=name, op=op) as transaction: # Use the global function
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

        sentry_sdk.add_breadcrumb( # Use the global function
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

        sentry_sdk.set_user(user_data) # Use the global function
        logger.debug(f"Set Sentry user context: {user_data.get('id', 'unknown')}")

    @staticmethod
    def set_tag(key: str, value: str):
        """
        Sets a custom tag for the current Sentry scope (global state).
        """
        if not SentryManager._initialized:
            logger.warning("SentryManager not initialized. Cannot set tag.")
            return

        sentry_sdk.set_tag(key, value) # Use the global function
        logger.debug(f"Set Sentry tag: {key}={value}")

    @staticmethod
    def set_extra(key: str, value: Any):
        """
        Sets custom extra data for the current Sentry scope (global state).
        """
        if not SentryManager._initialized:
            logger.warning("SentryManager not initialized. Cannot set extra data.")
            return

        sentry_sdk.set_extra(key, value) # Use the global function
        logger.debug(f"Set Sentry extra {key}")
