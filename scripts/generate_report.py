#!/usr/bin/env python3
"""
📊 Enterprise Analytics Report Generator
========================================
Generates comprehensive reports on bot usage, performance,
user sentiment, and system health based on Supabase data.
Supports various formats (CSV, JSON, HTML) and time ranges.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from supabase import create_client, Client as SupabaseClient
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot as plot_offline
import json

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REPORT_OUTPUT_DIR = Path(os.getenv("REPORT_OUTPUT_DIR", "./reports"))
REPORT_FORMAT = os.getenv("REPORT_FORMAT", "html") # Options: csv, json, html
DEFAULT_DAYS = int(os.getenv("DEFAULT_REPORT_DAYS", "7"))

def _get_supabase_client():
    """Creates and returns a Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Connected to Supabase for report generation.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise e

def _fetch_data(supabase_client: SupabaseClient, start_date: datetime, end_date: datetime):
    """Fetches conversation and performance data from Supabase."""
    logger.info(f"Fetching data from {start_date.isoformat()} to {end_date.isoformat()}")

    # Fetch conversation data
    try:
        conv_response = supabase_client.table("conversations") \
            .select("*") \
            .gte("timestamp", start_date.isoformat()) \
            .lte("timestamp", end_date.isoformat()) \
            .execute()
        conversations_df = pd.DataFrame(conv_response.data)
        logger.info(f"Fetched {len(conversations_df)} conversation records.")
    except Exception as e:
        logger.error(f"Failed to fetch conversation data: {e}")
        conversations_df = pd.DataFrame() # Return empty DataFrame on error

    # Fetch performance metrics data
    try:
        perf_response = supabase_client.table("performance_metrics") \
            .select("*") \
            .gte("timestamp", start_date.isoformat()) \
            .lte("timestamp", end_date.isoformat()) \
            .execute()
        performance_df = pd.DataFrame(perf_response.data)
        logger.info(f"Fetched {len(performance_df)} performance metric records.")
    except Exception as e:
        logger.error(f"Failed to fetch performance data: {e}")
        performance_df = pd.DataFrame() # Return empty DataFrame on error

    return conversations_df, performance_df

def _generate_summary_stats(conversations_df: pd.DataFrame, performance_df: pd.DataFrame):
    """Calculates summary statistics."""
    stats = {}
    if not conversations_df.empty:
        stats['total_interactions'] = len(conversations_df)
        stats['unique_users'] = conversations_df['user_id'].nunique()
        stats['avg_response_time'] = conversations_df['response_time_seconds'].mean() if 'response_time_seconds' in conversations_df.columns else 0.0
        stats['sentiment_breakdown'] = conversations_df['sentiment'].value_counts().to_dict() if 'sentiment' in conversations_df.columns else {}
        stats['intent_breakdown'] = conversations_df['intent'].value_counts().to_dict() if 'intent' in conversations_df.columns else {}
        stats['escalated_count'] = conversations_df[conversations_df['urgency'] == 'critical'].shape[0] + conversations_df[conversations_df['sentiment'] == 'very_negative'].shape[0]

    if not performance_df.empty:
        stats['api_call_duration_avg'] = performance_df[performance_df['metric_type'] == 'api_call_duration']['value'].mean()
        stats['db_query_duration_avg'] = performance_df[performance_df['metric_type'] == 'db_query_duration']['value'].mean()

    return stats

def _generate_charts(conversations_df: pd.DataFrame, performance_df: pd.DataFrame):
    """Generates Plotly charts."""
    charts = {}
    if not conversations_df.empty:
        # Convert timestamp to datetime if it's a string
        if 'timestamp' in conversations_df.columns:
            conversations_df['timestamp'] = pd.to_datetime(conversations_df['timestamp'])

        # Chart 1: Interactions Over Time
        if 'timestamp' in conversations_df.columns:
            daily_counts = conversations_df.groupby(conversations_df['timestamp'].dt.date).size()
            fig_interactions = px.line(x=daily_counts.index, y=daily_counts.values, title="Interactions Over Time")
            charts['interactions_over_time'] = fig_interactions

        # Chart 2: Sentiment Distribution
        if 'sentiment' in conversations_df.columns:
            sentiment_counts = conversations_df['sentiment'].value_counts()
            fig_sentiment = px.pie(values=sentiment_counts.values, names=sentiment_counts.index, title="Sentiment Distribution")
            charts['sentiment_distribution'] = fig_sentiment

        # Chart 3: Intent Distribution
        if 'intent' in conversations_df.columns:
            intent_counts = conversations_df['intent'].value_counts()
            fig_intent = px.bar(x=intent_counts.index, y=intent_counts.values, title="Intent Distribution")
            charts['intent_distribution'] = fig_intent

    if not performance_df.empty:
        # Chart 4: Performance Metric Trends (e.g., response time)
        if 'timestamp' in performance_df.columns and 'value' in performance_df.columns and 'metric_type' in performance_df.columns:
             perf_subset = performance_df[performance_df['metric_type'].isin(['response_time', 'api_call_duration'])]
             if not perf_subset.empty:
                 fig_perf = px.line(perf_subset, x='timestamp', y='value', color='metric_type', title="Performance Metrics Over Time")
                 charts['performance_trends'] = fig_perf


    return charts

def _save_report_html(stats: dict, charts: dict, output_path: Path):
    """Saves the report as an HTML file with embedded charts."""
    html_string = f"""
    <html>
        <head><title>College Bot Analytics Report - {datetime.now().date()}</title></head>
        <body>
            <h1>College Bot Analytics Report</h1>
            <h2>Summary Statistics (Last {DEFAULT_DAYS} Days)</h2>
            <ul>
    """
    for key, value in stats.items():
        html_string += f"<li><strong>{key}:</strong> {value}</li>\n"
    html_string += "</ul>"

    html_string += "<h2>Charts</h2>"
    for title, chart_fig in charts.items():
        chart_html = plot_offline(chart_fig, output_type='div', include_plotlyjs=False)
        html_string += f"<h3>{title.replace('_', ' ').title()}</h3>{chart_html}"

    html_string += """
        </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_string)
    logger.info(f"HTML report saved to {output_path}")

def _save_report_csv(stats: dict, conversations_df: pd.DataFrame, output_path: Path):
    """Saves the report data as a CSV file."""
    # Flatten stats dictionary for CSV header
    stats_flat = {}
    for k, v in stats.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                stats_flat[f"{k}_{sub_k}"] = sub_v
        else:
            stats_flat[k] = v

    # Create a DataFrame for stats
    stats_df = pd.DataFrame([stats_flat])

    # Combine with conversation data (or just save stats)
    # For simplicity, saving just stats here. Combine with conv_df if needed.
    stats_df.to_csv(output_path, index=False)
    logger.info(f"CSV report saved to {output_path}")

def _save_report_json(stats: dict, output_path: Path):
    """Saves the report data as a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=4, default=str) # default=str handles datetime objects
    logger.info(f"JSON report saved to {output_path}")

def generate_report(start_date: datetime, end_date: datetime, output_format: str):
    """Main report generation function."""
    logger.info(f"Starting report generation for {start_date.date()} to {end_date.date()}...")

    supabase_client = _get_supabase_client()
    conversations_df, performance_df = _fetch_data(supabase_client, start_date, end_date)

    stats = _generate_summary_stats(conversations_df, performance_df)
    charts = _generate_charts(conversations_df, performance_df)

    # Ensure output directory exists
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename_base = f"report_{start_date.date()}_to_{end_date.date()}"
    if output_format == "html":
        output_path = REPORT_OUTPUT_DIR / f"{filename_base}.html"
        _save_report_html(stats, charts, output_path)
    elif output_format == "csv":
        output_path = REPORT_OUTPUT_DIR / f"{filename_base}.csv"
        _save_report_csv(stats, conversations_df, output_path)
    elif output_format == "json":
        output_path = REPORT_OUTPUT_DIR / f"{filename_base}.json"
        _save_report_json(stats, output_path)
    else:
        logger.error(f"Unsupported output format: {output_format}")
        return

    logger.info("Report generation completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate analytics reports.")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD). Defaults to N days ago.")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--format", type=str, choices=["csv", "json", "html"], help="Output format (default: env var REPORT_FORMAT)")
    parser.add_argument("--days", type=int, help="Number of days back from today (default: env var DEFAULT_REPORT_DAYS)")

    args = parser.parse_args()

    # Determine dates
    end_date = datetime.now()
    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)
    elif args.days:
        end_date = datetime.now() - timedelta(days=args.days)

    start_date = end_date - timedelta(days=DEFAULT_DAYS)
    if args.start_date:
        start_date = datetime.fromisoformat(args.start_date)
    elif args.days:
        start_date = datetime.now() - timedelta(days=args.days)

    # Determine format
    output_format = REPORT_FORMAT
    if args.format:
        output_format = args.format

    try:
        generate_report(start_date, end_date, output_format)
    except Exception as e:
        logger.critical(f"Report generation failed: {e}")
        sys.exit(1)