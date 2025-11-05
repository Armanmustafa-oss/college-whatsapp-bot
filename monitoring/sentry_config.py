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
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Ensures only one instance of SentryManager exists."""
        if cls._instance is None:
            cls._instance = super(SentryManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(
        cls,
        dsn: str,
        environment: str,
        traces_sample_rate: float = 1.0,
        profiles_sample_rate: float = 1.0, # Enable profiling for performance insights
        release: Optional[str] = None,
        server_name: Optional[str] = None
    ):
        """
        Initializes the Sentry SDK with enterprise-grade settings.

        Args:
            dsn (str): The Sentry DSN.
            environment (str): The environment (e.g., 'development', 'staging', 'production').
            traces_sample_rate (float): Rate of transactions to capture traces for (0.0 to 1.0).
            profiles_sample_rate (float): Rate of transactions to capture profiles for (0.0 to 1.0).
            release (Optional[str]): The application release version.
            server_name (Optional[str]): Name of the server instance.
        """
        if cls._initialized:
            logger.warning("SentryManager already initialized. Skipping re-initialization.")
            return

        try:
            # Configure Sentry integrations
            integrations = [
                FastApiIntegration(transaction_style="endpoint"), # Capture FastAPI transactions
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR), # Capture logs as events
                # SqlalchemyIntegration(), # Uncomment if using SQLAlchemy directly
            ]

            sentry_sdk.init(
                dsn=dsn,
                integrations=integrations,
                environment=environment,
                traces_sample_rate=traces_sample_rate,
                profiles_sample_rate=profiles_sample_rate,
                release=release,
                server_name=server_name,
                # Performance and stability settings
                attach_stacktrace=True,
                send_default_pii=False, # Explicitly disable PII sending
                # Breadcrumbs for better context
                before_breadcrumb=cls._before_breadcrumb_callback,
                # Custom error handling
                before_send=cls._before_send_callback,
            )
            cls._initialized = True
            logger.info(f"✅ Sentry initialized for environment: {environment}")
        except Exception as e:
            logger.critical(f"❌ Failed to initialize Sentry: {e}")
            raise e # Re-raise to prevent app startup if Sentry is critical

    @staticmethod
    def _before_breadcrumb_callback(breadcrumb, hint):
        """
        Filters or modifies breadcrumbs before they are sent to Sentry.
        Useful for removing sensitive data or noise.
        """
        # Example: Filter out specific log messages
        if breadcrumb.get('category') == 'urllib3.connectionpool':
            return None # Drop this breadcrumb
        # Example: Redact sensitive query parameters from URLs
        if breadcrumb.get('type') == 'http' and 'data' in breadcrumb:
            url = breadcrumb['data'].get('url', '')
            # Implement redaction logic if needed (e.g., remove tokens from URL)
            # breadcrumb['data']['url'] = redact_url(url)
        return breadcrumb

    @staticmethod
    def _before_send_callback(event, hint):
        """
        Filters or modifies events before they are sent to Sentry.
        Useful for adding context, filtering, or scrubbing data.
        """
        # Example: Add custom tags based on event type
        if event.get('level') == 'error':
            event.setdefault('tags', {})['error_type'] = 'application_error'

        # Example: Scrub potentially sensitive data from contexts or extra
        # This is a basic example; use Sentry's data scrubbing rules for complex cases
        if 'extra' in event:
            for key in list(event['extra'].keys()):
                if 'token' in key.lower() or 'key' in key.lower():
                    event['extra'][key] = '[Filtered]'

        return event

    @classmethod
    def capture_exception_with_context(
        cls,
        exception: Exception,
        extra_context: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Captures an exception with rich, contextual information.

        Args:
            exception (Exception): The exception object.
            extra_context (Optional[Dict[str, Any]]): Additional context data.
            user_context (Optional[Dict[str, Any]]): User-related data (e.g., user_id, session_id).
            tags (Optional[Dict[str, str]]): Custom tags for filtering/searching.
        """
        if not cls._initialized:
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

        Args:
            name (str): Name of the transaction.
            op (str): Operation type (e.g., 'http.server', 'db.query').
        """
        if not cls._initialized:
            logger.warning("SentryManager not initialized. Transaction context manager is a no-op.")
            yield
            return

        with sentry_sdk.start_transaction(name=name, op=op) as transaction:
            logger.debug(f"Started Sentry transaction: {name}")
            yield transaction
            logger.debug(f"Finished Sentry transaction: {name}")

    @classmethod
    def add_breadcrumb(
        cls,
        message: str,
        category: str = "custom",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Adds a custom breadcrumb to the current Sentry scope.

        Args:
            message (str): The message for the breadcrumb.
            category (str): Category of the breadcrumb.
            level (str): Log level (e.g., 'info', 'warning', 'error').
            data (Optional[Dict[str, Any]]): Additional data to attach.
        """
        if not cls._initialized:
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

    @classmethod
    def set_user_context(cls, user_data: Dict[str, Any]):
        """
        Sets user context for the current Sentry scope.

        Args:
            user_data (Dict[str, Any]): User information (e.g., id, username, ip_address).
        """
        if not cls._initialized:
            logger.warning("SentryManager not initialized. Cannot set user context.")
            return

        sentry_sdk.set_user(user_data)
        logger.debug(f"Set Sentry user context: {user_data.get('id', 'unknown')}")

    @classmethod
    def set_tag(cls, key: str, value: str):
        """
        Sets a custom tag for the current Sentry scope.

        Args:
            key (str): Tag name.
            value (str): Tag value.
        """
        if not cls._initialized:
            logger.warning("SentryManager not initialized. Cannot set tag.")
            return

        sentry_sdk.set_tag(key, value)
        logger.debug(f"Set Sentry tag: {key}={value}")

    @classmethod
    def set_extra(cls, key: str, value: Any):
        """
        Sets custom extra data for the current Sentry scope.

        Args:
            key (str): Data key.
            value (Any): Data value.
        """
        if not cls._initialized:
            logger.warning("SentryManager not initialized. Cannot set extra data.")
            return

        sentry_sdk.set_extra(key, value)
        logger.debug(f"Set Sentry extra data: {key}")


# Example usage (if run as main):
# if __name__ == "__main__":
#     # Example initialization (requires a real DSN)
#     # SentryManager.initialize(
#     #     dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
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