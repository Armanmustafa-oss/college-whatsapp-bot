"""
⚡ Enterprise Performance & Metrics Collection Engine
=======================================================
Advanced performance tracking, metric aggregation, and
real-time health monitoring for the bot application.
Integrates with Supabase for metric persistence and analysis.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from supabase import Client as SupabaseClient
from datetime import datetime, timezone
import threading
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Enumeration for different types of performance metrics."""
    RESPONSE_TIME = "response_time"
    API_CALL_DURATION = "api_call_duration"
    DB_QUERY_DURATION = "db_query_duration"
    ERROR_RATE = "error_rate"
    CONCURRENT_USERS = "concurrent_users"
    RATE_LIMIT_HIT = "rate_limit_hit"
    CONVERSATION_COUNT = "conversation_count"
    SENTIMENT_SCORE = "sentiment_score"

@dataclass
class PerformanceMetric:
    """Represents a single performance metric instance."""
    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] # e.g., {"intent": "admissions", "endpoint": "/webhook"}
    unit: str = "seconds" # Default unit

class PerformanceTracker:
    """
    Centralized tracker for application performance metrics.
    Collects, aggregates, and optionally persists metrics to Supabase.
    Provides methods for real-time monitoring and alerting.
    """
    def __init__(self, supabase_client: Optional[SupabaseClient] = None, metrics_buffer_size: int = 1000):
        """
        Initializes the PerformanceTracker.

        Args:
            supabase_client (Optional[SupabaseClient]): Supabase client for metric persistence.
            metrics_buffer_size (int): Size of the in-memory buffer for metrics before flush.
        """
        self.supabase = supabase_client
        self.metrics_buffer: List[PerformanceMetric] = deque(maxlen=metrics_buffer_size)
        self.metrics_lock = threading.Lock() # Thread-safe access to buffer
        self.aggregated_metrics: Dict[str, List[float]] = defaultdict(list)
        self.aggregated_metrics_lock = threading.Lock()

        # Define thresholds for alerting
        self.alert_thresholds = {
            MetricType.RESPONSE_TIME: {"warning": 2.0, "critical": 5.0}, # seconds
            MetricType.ERROR_RATE: {"warning": 0.05, "critical": 0.10}, # percentage
            # Add more thresholds as needed
        }
        logger.info("PerformanceTracker initialized.")

    def log_metric(self, metric_type: MetricType, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Logs a single performance metric.

        Args:
            metric_type (MetricType): The type of metric.
            value (float): The metric value.
            tags (Optional[Dict[str, str]]): Optional tags for categorization.
        """
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(timezone.utc),
            tags=tags or {}
        )
        with self.metrics_lock:
            self.metrics_buffer.append(metric)

        # Aggregate for quick access (e.g., for health checks)
        key = f"{metric_type.value}_" + "_".join(f"{k}={v}" for k, v in sorted((tags or {}).items()))
        with self.aggregated_metrics_lock:
            self.aggregated_metrics[key].append(value)
            # Keep only the last N values for aggregation (e.g., last 100 for avg/percentiles)
            if len(self.aggregated_metrics[key]) > 100:
                self.aggregated_metrics[key] = self.aggregated_metrics[key][-100:]

        # Check for alerts based on thresholds
        self._check_alerts(metric)

    def log_response_time(self, duration: float, intent: str = "general"):
        """Convenience method for logging response times."""
        self.log_metric(
            MetricType.RESPONSE_TIME,
            duration,
            tags={"intent": intent}
        )

    def log_api_call_duration(self, duration: float, api_name: str):
        """Convenience method for logging API call durations."""
        self.log_metric(
            MetricType.API_CALL_DURATION,
            duration,
            tags={"api": api_name}
        )

    def log_db_query_duration(self, duration: float, query_type: str = "unknown"):
        """Convenience method for logging database query durations."""
        self.log_metric(
            MetricType.DB_QUERY_DURATION,
            duration,
            tags={"query_type": query_type}
        )

    def log_error_event(self, error_type: str = "general"):
        """Convenience method for logging error occurrences."""
        # This would typically increment a counter, which is harder to represent as a float.
        # For now, we log a value of 1.0 for each error event.
        self.log_metric(
            MetricType.ERROR_RATE,
            1.0, # Represents one error event
            tags={"error_type": error_type}
        )

    def log_rate_limit_event(self, user_id: str):
        """Convenience method for logging rate limit hits."""
        self.log_metric(
            MetricType.RATE_LIMIT_HIT,
            1.0, # Represents one rate limit hit
            tags={"user_id": user_id}
        )

    def _check_alerts(self, metric: PerformanceMetric):
        """Checks if a logged metric exceeds defined alert thresholds."""
        threshold_config = self.alert_thresholds.get(metric.metric_type)
        if not threshold_config:
            return # No thresholds defined for this metric type

        # This is a simple check. A more robust system might calculate rates over time windows.
        if metric.metric_type in [MetricType.RESPONSE_TIME, MetricType.ERROR_RATE]:
            if metric.value > threshold_config["critical"]:
                logger.critical(f"🚨 CRITICAL ALERT: {metric.metric_type.value} = {metric.value} exceeded critical threshold ({threshold_config['critical']}). Tags: {metric.tags}")
                # Here you could integrate with an alerting system (e.g., Slack webhook, PagerDuty)
            elif metric.value > threshold_config["warning"]:
                logger.warning(f"⚠️ WARNING: {metric.metric_type.value} = {metric.value} exceeded warning threshold ({threshold_config['warning']}). Tags: {metric.tags}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Retrieves aggregated metrics for the current state (e.g., for a /metrics endpoint).

        Returns:
            Dict[str, Any]: A dictionary containing aggregated metric values.
        """
        aggregated_snapshot = {}
        with self.aggregated_metrics_lock:
            for key, values in self.aggregated_metrics.items():
                if values: # Only calculate if there are values
                    try:
                        aggregated_snapshot[key] = {
                            "count": len(values),
                            "avg": round(statistics.mean(values), 4),
                            "min": round(min(values), 4),
                            "max": round(max(values), 4),
                            "p95": round(statistics.quantiles(values, n=20)[-1], 4) if len(values) >= 20 else None # 95th percentile
                        }
                    except statistics.StatisticsError:
                         # Handle case where quantiles cannot be calculated (e.g., not enough data)
                         aggregated_snapshot[key] = {
                            "count": len(values),
                            "avg": round(statistics.mean(values), 4),
                            "min": round(min(values), 4),
                            "max": round(max(values), 4),
                            "p95": "N/A (insufficient data)"
                        }
        return aggregated_snapshot

    def flush_metrics_to_supabase(self, table_name: str = "performance_metrics"):
        """
        Flushes the in-memory metrics buffer to Supabase for long-term storage and analysis.

        Args:
            table_name (str): The name of the Supabase table to insert metrics into.
        """
        if not self.supabase:
            logger.warning("Supabase client not provided. Cannot flush metrics.")
            return

        with self.metrics_lock:
            metrics_to_flush = list(self.metrics_buffer)
            self.metrics_buffer.clear() # Clear the buffer after copying

        if not metrics_to_flush:
            logger.debug("No metrics to flush to Supabase.")
            return

        # Prepare data for Supabase insertion
        supabase_records = []
        for metric in metrics_to_flush:
            record = {
                "metric_type": metric.metric_type.value,
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(), # Supabase timestamp
                "tags": metric.tags, # Supabase supports JSON columns
                "unit": metric.unit
            }
            supabase_records.append(record)

        try:
            # Insert metrics into Supabase
            self.supabase.table(table_name).insert(supabase_records).execute()
            logger.info(f"Flushed {len(supabase_records)} metrics to Supabase table '{table_name}'.")
        except Exception as e:
            logger.error(f"Failed to flush metrics to Supabase: {e}")
            # Re-add failed metrics back to the buffer (or a separate retry buffer)
            with self.metrics_lock:
                self.metrics_buffer.extendleft(reversed(metrics_to_flush)) # Maintain order

    async def background_flush_loop(self, interval_seconds: int = 30, table_name: str = "performance_metrics"):
        """
        An async background task to periodically flush metrics to Supabase.

        Args:
            interval_seconds (int): Interval between flushes.
            table_name (str): The Supabase table name.
        """
        if not self.supabase:
             logger.info("Background flush loop not started: Supabase client not provided.")
             return

        logger.info(f"Starting background metrics flush loop (interval: {interval_seconds}s)...")
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                self.flush_metrics_to_supabase(table_name)
            except asyncio.CancelledError:
                logger.info("Background metrics flush loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in background metrics flush loop: {e}")


# Example usage (if run as main):
# import asyncio
# if __name__ == "__main__":
#     # Example: Initialize with a mock Supabase client (replace with real one)
#     # mock_supabase = create_client("...", "...")
#     tracker = PerformanceTracker(supabase_client=None) # No Supabase for this example
#
#     # Log some metrics
#     tracker.log_response_time(1.23, "admissions")
#     tracker.log_response_time(0.87, "admissions")
#     tracker.log_response_time(3.45, "fees") # This might trigger a warning if threshold is 2.0
#     tracker.log_api_call_duration(0.5, "groq_api")
#
#     # Get current aggregated metrics
#     current_metrics = tracker.get_current_metrics()
#     print("Current Aggregated Metrics:", current_metrics)
#
#     # Example of background flush (requires Supabase client)
#     # async def run_flusher():
#     #     await tracker.background_flush_loop(interval_seconds=10)
#     #
#     # asyncio.run(run_flusher())