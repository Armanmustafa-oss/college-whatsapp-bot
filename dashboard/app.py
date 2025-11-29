"""
🚀 Enterprise Command Center: College Bot Analytics Dashboard
===============================================================
Enhanced, role-based, interactive dashboard powered by FastAPI and Plotly.
Monitors bot performance, user engagement, sentiment, and operational health.
Simulates Fortune 500 grade features within a single-file application.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta, timezone
import json
from typing import Dict, List, Optional, Tuple
import numpy as np # For handling NaN values and calculations
import calendar # For peak hour analysis

# Import configuration (adjust import path if necessary)
from bot.config import SUPABASE_URL, SUPABASE_KEY, ENVIRONMENT, PORT

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO if ENVIRONMENT != "development" else logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Global Variables for Supabase Client ---
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from supabase import Client as SupabaseClient
supabase: Optional['SupabaseClient'] = None

# --- Application Lifecycle Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manitors application startup and shutdown tasks for the dashboard.
    """
    global supabase
    logger.info("🚀 Starting up Enhanced College Bot Dashboard...")

    # Initialize Supabase Client for data fetching
    try:
        from supabase import create_client, Client as SupabaseClient
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Connected to Supabase for dashboard data.")
    except Exception as e:
        logger.critical(f"❌ Failed to connect to Supabase for dashboard: {e}")
        supabase = None # Allow app to start, but metrics will be mocked

    yield # Hand over control to the application

    # Shutdown tasks
    logger.info("🛑 Shutting down Enhanced College Bot Dashboard...")

# --- Initialize FastAPI App ---
app = FastAPI(
    title="Enhanced College Bot Analytics Dashboard",
    description="Enterprise-grade analytics dashboard for monitoring the college WhatsApp bot.",
    version="4.0.0",
    lifespan=lifespan
)

# --- Constants for Calculations ---
# Hypothetical values for cost savings and efficiency calculations
AVERAGE_MANUAL_HANDLING_TIME_MINS = 5 # Average time to handle a query manually
COST_PER_MANUAL_INTERACTION_USD = 2.50 # Hypothetical cost to handle one query manually
TARGET_UPTIME_PERCENT = 99.9 # Target uptime percentage

# --- Data Fetching Helper Functions ---
async def fetch_raw_conversation_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetches raw conversation data from Supabase and returns a DataFrame."""
    if not supabase:
        logger.warning("Supabase client not configured; returning empty DataFrame.")
        return pd.DataFrame()

    try:
        query = supabase.table("conversations") \
            .select("id, timestamp, sentiment, response_time_seconds, intent, urgency, user_id") \
            .gte("timestamp", start_date.isoformat()) \
            .lte("timestamp", end_date.isoformat())

        response = query.execute()
        data = response.data
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
        return df
    except Exception as e:
        logger.error(f"Error fetching raw conversation data: {e}")
        return pd.DataFrame()

def calculate_executive_metrics(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> Dict:
    """Calculates metrics for the Executive Dashboard."""
    total_interactions = len(df)
    avg_response_time = float(df['response_time_seconds'].mean()) if 'response_time_seconds' in df.columns and not df['response_time_seconds'].empty else 0.0
    avg_response_time = avg_response_time if pd.notna(avg_response_time) else 0.0

    # Calculate Automation Rate (assuming no 'manual_resolution' flag, we estimate based on response time or urgency/sentiment)
    # For simplicity, let's consider interactions with low urgency and positive/neutral sentiment as automated
    automated_interactions = df[
        ((df['urgency'] == 'low') | (df['urgency'] == 'medium')) &
        ((df['sentiment'] == 'positive') | (df['sentiment'] == 'neutral'))
    ].shape[0]
    automation_rate = (automated_interactions / total_interactions * 100) if total_interactions > 0 else 0.0

    # Calculate Staff Hours Saved
    total_manual_time_saved_secs = total_interactions * AVERAGE_MANUAL_HANDLING_TIME_MINS * 60
    total_manual_time_saved_hours = total_manual_time_saved_secs / 3600
    staff_hours_saved = round(total_manual_time_saved_hours, 2)

    # Calculate Cost Savings (using hypothetical cost)
    cost_if_manual_usd = total_interactions * COST_PER_MANUAL_INTERACTION_USD
    # Assuming bot operation cost is negligible compared to manual handling for this calc
    cost_savings_usd = round(cost_if_manual_usd, 2) # This is the saving compared to manual handling

    # Calculate ROI (Investment needed for bot is not included here, so this is a simplified calculation)
    # ROI = (Gain from Investment - Cost of Investment) / Cost of Investment
    # Simplified: ROI = (Cost Savings) / (Hypothetical Annual Bot Op Cost)
    # Let's assume a hypothetical annual cost for bot operation for ROI calc
    hypothetical_annual_bot_cost_usd = 50000 # Placeholder value
    # Calculate savings for the period
    period_days = (end_date - start_date).days
    period_pro_rata_bot_cost = (hypothetical_annual_bot_cost_usd / 365) * period_days
    roi_percentage = ((cost_savings_usd - period_pro_rata_bot_cost) / period_pro_rata_bot_cost * 100) if period_pro_rata_bot_cost > 0 else 0.0

    # Calculate Satisfaction Score (1-5 based on sentiment distribution)
    sentiment_counts = df['sentiment'].value_counts()
    total_sentiment_count = sentiment_counts.sum()
    if total_sentiment_count > 0:
        # Assign scores: very_negative=1, negative=2, neutral=3, positive=4
        satisfaction_score_raw = (
            (sentiment_counts.get('very_negative', 0) * 1) +
            (sentiment_counts.get('negative', 0) * 2) +
            (sentiment_counts.get('neutral', 0) * 3) +
            (sentiment_counts.get('positive', 0) * 4)
        ) / total_sentiment_count
        # Normalize to 1-5 scale
        satisfaction_score = round(satisfaction_score_raw, 2)
    else:
        satisfaction_score = 0.0

    return {
        "cost_savings": cost_savings_usd,
        "roi_percentage": round(roi_percentage, 2),
        "total_conversations": total_interactions,
        "satisfaction_score": satisfaction_score,
        "avg_response_time": round(avg_response_time, 2),
        "automation_rate": round(automation_rate, 2),
        "staff_hours_saved": staff_hours_saved
    }

def calculate_technical_metrics(df: pd.DataFrame) -> Dict:
    """Calculates metrics for the Technical Dashboard."""
    total_interactions = len(df)
    if total_interactions == 0:
        return {
            "uptime": 0.0, "avg_response_time": 0.0, "p95_response_time": 0.0, "p99_response_time": 0.0,
            "error_rate": 0.0, "active_sessions": 0, "recent_errors": []
        }

    # Uptime: Assume uptime based on last interaction time (simplified)
    # This is a placeholder - true uptime needs external monitoring
    current_time = datetime.now(timezone.utc)
    if not df.empty:
        last_interaction_time = df['timestamp'].max()
        time_since_last = (current_time - last_interaction_time).total_seconds()
        # Assume system is down if no interaction in last 10 minutes (configurable)
        downtime_secs = time_since_last if time_since_last > 600 else 0
        # Calculate uptime % for the period covered by df (or a fixed window)
        # For this example, we'll just report a static high uptime if recent data exists
        uptime = TARGET_UPTIME_PERCENT # Placeholder for actual uptime calc
    else:
        uptime = 0.0

    response_times = df['response_time_seconds'].dropna()
    avg_response_time = float(response_times.mean()) if not response_times.empty else 0.0
    p95_response_time = float(response_times.quantile(0.95)) if not response_times.empty else 0.0
    p99_response_time = float(response_times.quantile(0.99)) if not response_times.empty else 0.0

    # Error Rate: Count very_negative sentiment as a proxy for errors or poor responses
    # In a real system, you'd have an 'error' flag in the DB
    error_count = df[df['sentiment'] == 'very_negative'].shape[0]
    error_rate = (error_count / total_interactions * 100) if total_interactions > 0 else 0.0

    # Active Sessions: Count unique users in the last 10 minutes (simplified)
    # This requires user session tracking which is not in the basic schema
    # Placeholder: Count unique users in the dataset as a proxy for unique interactions
    unique_users = df['user_id'].nunique() if 'user_id' in df.columns else 0
    active_sessions = unique_users # Placeholder

    # Recent Errors: Find conversations with 'very_negative' sentiment
    # In a real system, this would come from an 'errors' table
    recent_errors_df = df[df['sentiment'] == 'very_negative'].tail(50) # Get last 50 'errors'
    recent_errors = []
    for _, row in recent_errors_df.iterrows():
        recent_errors.append({
            "timestamp": row['timestamp'].isoformat(),
            "message": f"High negative sentiment detected for intent: {row.get('intent', 'N/A')}",
            "severity": "HIGH"
        })

    return {
        "uptime": round(uptime, 2),
        "avg_response_time": round(avg_response_time, 2),
        "p95_response_time": round(p95_response_time, 2),
        "p99_response_time": round(p99_response_time, 2),
        "error_rate": round(error_rate, 2),
        "active_sessions": active_sessions, # Placeholder
        "recent_errors": recent_errors
    }

def calculate_analytics_metrics(df: pd.DataFrame) -> Dict:
    """Calculates metrics for the Analytics Dashboard."""
    total_interactions = len(df)
    unique_users = df['user_id'].nunique() if 'user_id' in df.columns and not df.empty else 0

    # Intent Distribution
    intent_counts = df['intent'].value_counts().to_dict() if 'intent' in df.columns and not df.empty else {}

    # Sentiment Distribution
    sentiment_counts = df['sentiment'].value_counts().to_dict() if not df.empty else {}

    # Language Usage (if available in context, not currently in schema)
    # language_counts = df['language_code'].value_counts().to_dict() if 'language_code' in df.columns else {}

    # Peak Hours Analysis (Hourly Volume)
    peak_hours_data = df['hour'].value_counts().sort_index().to_dict() if not df.empty else {}

    # Top 5 Intents
    top_5_intents = dict(list(intent_counts.items())[:5]) if intent_counts else {}

    # Growth Rate (simplified: compare with previous period of same length)
    # This requires fetching previous period data, simplified here
    # growth_rate = ((current_period_count - previous_period_count) / previous_period_count * 100) if previous_period_count > 0 else 0

    # Average Conversation Length (Assuming 1 row = 1 interaction/message)
    # This is implicitly 1 if each row is a message. If rows represent sessions, this would be different.
    avg_conversation_length = 1.0 # Placeholder, needs session data

    # Returning Users (requires historical user data across periods, simplified)
    # returning_users_pct = ... # Requires complex historical analysis

    return {
        "total_conversations": total_interactions,
        "unique_users": unique_users,
        "intent_distribution": intent_counts,
        "sentiment_distribution": sentiment_counts,
        # "language_usage": language_counts, # Not available in basic schema
        "peak_hours": peak_hours_data,
        "top_5_intents": top_5_intents,
        "avg_conversation_length": avg_conversation_length, # Placeholder
        # "returning_users_pct": returning_users_pct, # Requires historical data
    }

# --- Chart Generation Functions ---
def create_cost_savings_trend_chart(start_date: datetime, end_date: datetime) -> str:
    """Simulates a cost savings trend chart."""
    # Generate mock data for the period
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    # Simulate increasing savings over time
    cumulative_savings = [i * 100 + np.random.normal(0, 50) for i in range(len(dates))] # Add some noise
    cumulative_savings = np.maximum(cumulative_savings, 0) # Ensure non-negative
    df = pd.DataFrame({'date': dates, 'cumulative_savings_usd': cumulative_savings})

    fig = px.line(df, x='date', y='cumulative_savings_usd', title="Cumulative Cost Savings Over Time (Simulated)")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        title_font_size=16,
        hovermode='x unified'
    )
    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_roi_over_time_chart(start_date: datetime, end_date: datetime) -> str:
    """Simulates an ROI over time chart."""
    # Generate mock data for the period
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    # Simulate increasing ROI over time
    roi_values = [i * 2 + np.random.normal(0, 1) for i in range(len(dates))] # Add some noise
    df = pd.DataFrame({'date': dates, 'roi_percentage': roi_values})

    # Use go.Figure with Scatter trace and fill='tonexty' for the fill effect
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['roi_percentage'],
        mode='lines', # Use 'lines' or 'lines+markers'
        fill='tonexty', # Fill down to the next trace (or to zero if it's the last trace)
        fillcolor='rgba(187, 134, 252, 0.2)', # Semi-transparent color (optional, adjust as needed)
        line=dict(color='rgba(187, 134, 252, 1)'), # Line color (adjust as needed, e.g., using --accent-color)
        name='ROI %' # Legend name
    ))

    fig.update_layout(
        title="ROI Over Time (Simulated)",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        title_font_size=16,
        hovermode='x unified'
    )
    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_query_volume_by_dept_chart(intent_counts: Dict[str, int]) -> str:
    """Creates a pie chart for query volume by department/intent."""
    if not intent_counts:
        fig = go.Figure(data=[go.Pie(labels=['No Data'], values=[1])])
        fig.update_layout(title="Query Volume by Intent (No Data)", template="plotly_dark", font=dict(color="white"))
    else:
        # Sort intents by count descending for better visual hierarchy
        sorted_items = sorted(intent_counts.items(), key=lambda item: item[1], reverse=True)
        sorted_names, sorted_values = zip(*sorted_items) if sorted_items else ([], [])
        fig = px.pie(values=sorted_values, names=sorted_names, title="Query Volume by Intent")
        fig.update_layout(template="plotly_dark", font=dict(color="white"))

    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_peak_hours_heatmap(peak_hours_data: Dict[int, int]) -> str:
    """Creates a heatmap for peak usage hours."""
    if not peak_hours_data:
        # Create an empty heatmap
        fig = go.Figure(data=go.Heatmap(z=[[0]*24], x=list(range(24)), y=['Activity'], colorscale='Blues'))
        fig.update_layout(title="Peak Usage Hours (No Data)", template="plotly_dark", font=dict(color="white"))
    else:
        # Prepare data for 24 hours
        hours = list(range(24))
        counts = [peak_hours_data.get(h, 0) for h in hours]
        # Use a single day for the y-axis for simplicity, or use day of week if available
        # For a true heatmap, you'd need data per day per hour
        # Here, we'll just show a bar-like heatmap for the aggregated counts
        z_data = [counts] # Single row
        y_labels = ['Hourly Volume'] # Placeholder label

        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=hours,
            y=y_labels,
            colorscale='Blues',
            text=counts, # Show count on each cell
            texttemplate="%{text}",
            textfont={"size": 12, "color": "white"},
            hoverongaps=False,
            hovertemplate='Hour: %{x}<br>Count: %{z}<extra></extra>'
        ))
        fig.update_layout(
            title="Peak Usage Hours (Aggregated)",
            template="plotly_dark",
            font=dict(color="white"),
            xaxis_title="Hour of Day (0-23)",
            yaxis_title="",
            yaxis={'showticklabels': False} # Hide y-axis label as it's not meaningful here
        )

    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_top_topics_chart(top_5_intents: Dict[str, int]) -> str:
    """Creates a horizontal bar chart for top 5 requested topics."""
    if not top_5_intents:
        fig = go.Figure(data=[go.Bar(x=[0], y=['No Data'], orientation='h')])
        fig.update_layout(title="Top 5 Requested Topics (No Data)", template="plotly_dark", font=dict(color="white"))
    else:
        intents = list(top_5_intents.keys())
        counts = list(top_5_intents.values())
        fig = px.bar(x=counts, y=intents, orientation='h', title="Top 5 Requested Topics")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            yaxis={'categoryorder':'total ascending'} # Order bars by count ascending (bottom to top)
        )

    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_sentiment_trend_chart(df: pd.DataFrame) -> str:
    """Creates a line chart for sentiment trend over time."""
    if df.empty or 'date' not in df.columns or 'sentiment' not in df.columns:
        fig = px.line(title="Sentiment Trend Over Time (No Data)")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            hovermode='x unified'
        )
        return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

    # Group by date and sentiment
    daily_sentiment = df.groupby(['date', 'sentiment']).size().reset_index(name='count')
    # Pivot for plotting
    pivot_df = daily_sentiment.pivot(index='date', columns='sentiment', values='count').fillna(0).reset_index()

    fig = px.line(pivot_df, x='date', y=pivot_df.columns[1:], title="Sentiment Trend Over Time") # Plot all sentiment columns
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        title_font_size=16,
        hovermode='x unified'
    )
    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_response_time_trend_chart(df: pd.DataFrame) -> str:
    """Creates a multi-line chart for response time trends (avg, p95, p99)."""
    if df.empty or 'timestamp' not in df.columns or 'response_time_seconds' not in df.columns:
        fig = px.line(title="Response Time Trends (Avg, P95, P99) (No Data)")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            hovermode='x unified'
        )
        return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

    # Ensure 'timestamp' is the index and is datetime type
    df_indexed = df.set_index('timestamp')
    # Resample to daily average, p95, p99
    # Use specific quantile functions to avoid lambda issues if possible, or handle lambda results carefully
    df_resampled = df_indexed.resample('D')['response_time_seconds'].agg(
        avg='mean',
        p95=lambda x: x.quantile(0.95),
        p99=lambda x: x.quantile(0.99)
    ).reset_index() # Reset index to make 'timestamp' a column again

    # Debug: Print column info (optional, remove after confirming fix)
    # print(f"df_resampled dtypes: {df_resampled.dtypes}")
    # print(f"df_resampled head: {df_resampled.head()}")

    # Explicitly convert the metric columns to float to ensure consistency
    # This handles potential object types resulting from lambda or quantile operations on empty groups
    numeric_cols = ['avg', 'p95', 'p99']
    for col in numeric_cols:
        if col in df_resampled.columns:
             # Convert to numeric, coercing errors (like NaN strings) to NaN
             df_resampled[col] = pd.to_numeric(df_resampled[col], errors='coerce')
             # Fill NaN values with a suitable value (e.g., 0) or interpolate
             # Filling with 0 might be misleading, interpolation is often better if appropriate
             # df_resampled[col] = df_resampled[col].fillna(0)
             # Or, drop rows where all y-values are NaN (if a day has no data)
             # df_resampled = df_resampled.dropna(subset=numeric_cols, how='all')
             # Or, use ffill/bfill/interpolate, e.g.:
             df_resampled[col] = df_resampled[col].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')

    # Check again if data is sufficient after processing
    if df_resampled.empty or df_resampled[numeric_cols].isna().all().all():
        fig = px.line(title="Response Time Trends (Avg, P95, P99) (No Valid Data After Processing)")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            hovermode='x unified'
        )
        return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

    # Now, attempt to create the plot with the processed DataFrame
    try:
        fig = px.line(df_resampled, x='timestamp', y=numeric_cols, title="Response Time Trends (Avg, P95, P99)")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            hovermode='x unified'
        )
        return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})
    except ValueError as e:
        logger.error(f"Error creating response time trend chart after processing: {e}")
        # Fallback chart if px.line still fails after processing
        fig = px.line(title=f"Response Time Trends (Error: {e})")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            hovermode='x unified'
        )
        return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_error_log_table(recent_errors: List[Dict]) -> str:
    """Creates an HTML table for the error log."""
    if not recent_errors:
        return "<p>No recent errors detected.</p>"

    table_html = """
    <table style="width: 100%; border-collapse: collapse; color: inherit;">
        <thead>
            <tr style="background-color: rgba(255,255,255,0.1); text-align: left;">
                <th style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">Timestamp</th>
                <th style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">Message</th>
                <th style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">Severity</th>
            </tr>
        </thead>
        <tbody>
    """
    for error in recent_errors:
        severity_color = "#FF4136" if error['severity'] == "HIGH" else "#FFDC00" # Red for high, Yellow for others
        table_html += f"""
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 8px;">{error['timestamp']}</td>
                <td style="padding: 8px;">{error['message']}</td>
                <td style="padding: 8px; color: {severity_color};">{error['severity']}</td>
            </tr>
        """
    table_html += """
        </tbody>
    </table>
    """
    return table_html

# --- FastAPI Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Renders the main enhanced dashboard page."""
    # Fetch data for the dashboard (last 7 days by default)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)

    raw_df = await fetch_raw_conversation_data(start_date, end_date)

    # Calculate metrics for different roles
    exec_metrics = calculate_executive_metrics(raw_df, start_date, end_date)
    tech_metrics = calculate_technical_metrics(raw_df)
    analytics_metrics = calculate_analytics_metrics(raw_df)

    # Generate charts
    cost_savings_chart = create_cost_savings_trend_chart(start_date, end_date)
    roi_chart = create_roi_over_time_chart(start_date, end_date)
    dept_volume_chart = create_query_volume_by_dept_chart(analytics_metrics.get("intent_distribution", {}))
    peak_hours_chart = create_peak_hours_heatmap(analytics_metrics.get("peak_hours", {}))
    top_topics_chart = create_top_topics_chart(analytics_metrics.get("top_5_intents", {}))
    sentiment_trend_chart = create_sentiment_trend_chart(raw_df)
    response_time_trend_chart = create_response_time_trend_chart(raw_df)
    error_log_html = create_error_log_table(tech_metrics.get("recent_errors", []))

    # --- Enhanced HTML Template with Role-Based Views ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enterprise Command Center</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            :root {{
                --primary-color: #1e3a8a;
                --secondary-color: #0d9488;
                --accent-color: #f59e0b;
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --danger-color: #ef4444;
                --text-primary: #e2e8f0;
                --text-secondary: #94a3b8;
                --bg-primary: #0f172a;
                --bg-secondary: #1e293b;
                --bg-card: #1e293b; /* Darker card background */
                --border-color: #334155;
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }}

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Inter', 'Roboto', 'Segoe UI', sans-serif;
            }}

            body {{
                background-color: var(--bg-primary);
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}

            /* Header */
            .header {{
                background-color: var(--bg-secondary);
                padding: 16px 32px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border-color);
            }}

            .logo {{
                font-size: 20px;
                font-weight: bold;
                color: var(--accent-color);
            }}

            .nav-controls {{
                display: flex;
                gap: 16px;
                align-items: center;
            }}

            .role-selector, .date-picker, .refresh-btn {{
                background-color: var(--bg-card);
                color: var(--text-primary);
                border: 1px solid var(--border-color);
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 14px;
            }}

            .refresh-btn {{
                background-color: var(--primary-color);
                color: white;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 4px;
            }}

            /* Main Layout */
            .main-container {{
                display: flex;
                flex: 1;
                overflow: hidden;
            }}

            /* Sidebar */
            .sidebar {{
                width: 220px;
                background-color: var(--bg-secondary);
                padding: 24px 12px;
                border-right: 1px solid var(--border-color);
                overflow-y: auto;
            }}

            .nav-item {{
                color: var(--text-secondary);
                text-decoration: none;
                display: block;
                padding: 10px 16px;
                border-radius: 4px;
                margin-bottom: 4px;
                transition: background-color 0.2s ease, color 0.2s ease;
                font-size: 14px;
            }}

            .nav-item:hover, .nav-item.active {{
                background-color: rgba(255, 255, 255, 0.1);
                color: var(--text-primary);
            }}

            /* Content Area */
            .content {{
                flex: 1;
                padding: 24px;
                overflow-y: auto;
            }}

            .dashboard-title {{
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 24px;
            }}

            /* Dashboard Views (Initially hidden) */
            .dashboard-view {{
                display: none;
            }}

            .dashboard-view.active {{
                display: block;
            }}

            /* Grid Layout for Metrics */
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }}

            /* Metric Card */
            .metric-card {{
                background-color: var(--bg-card);
                border-radius: 8px;
                padding: 16px;
                box-shadow: var(--shadow);
                transition: transform 0.2s ease;
            }}

            .metric-card:hover {{
                transform: translateY(-4px);
            }}

            .metric-label {{
                color: var(--text-secondary);
                font-size: 12px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }}

            .metric-value {{
                font-size: 24px;
                font-weight: 700;
                color: var(--text-primary);
            }}

            .metric-change {{
                font-size: 12px;
                color: var(--success-color); /* Default green for positive change */
            }}

            .metric-change.negative {{
                color: var(--danger-color);
            }}

            /* Chart Card */
            .chart-card {{
                background-color: var(--bg-card);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 24px;
                box-shadow: var(--shadow);
            }}

            .chart-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }}

            .chart-title {{
                font-size: 16px;
                font-weight: 600;
                color: var(--text-primary);
            }}

            .chart-actions {{
                display: flex;
                gap: 8px;
            }}

            .chart-btn {{
                background: none;
                border: 1px solid var(--border-color);
                color: var(--text-secondary);
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }}

            .chart-btn:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                color: var(--text-primary);
            }}

            .chart-container {{
                width: 100%;
            }}

            /* Table Card */
            .table-card {{
                background-color: var(--bg-card);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 24px;
                box-shadow: var(--shadow);
                overflow-x: auto; /* Allow horizontal scroll for tables */
            }}

            /* Loading Skeleton */
            .skeleton {{
                background: linear-gradient(90deg, var(--bg-card) 25%, rgba(255, 255, 255, 0.1) 50%, var(--bg-card) 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 4px;
            }}

            @keyframes loading {{
                0% {{ background-position: 200% 0; }}
                100% {{ background-position: -200% 0; }}
            }}

            /* Responsive Adjustments */
            @media (max-width: 768px) {{
                .header {{
                    flex-direction: column;
                    gap: 16px;
                    padding: 16px;
                }}
                .nav-controls {{
                    width: 100%;
                    justify-content: center;
                }}
                .sidebar {{
                    width: 60px;
                    align-items: center;
                }}
                .sidebar .nav-item span {{
                    display: none;
                }}
                .sidebar .nav-item::before {{
                    content: attr(data-icon); /* Requires icons to be added as data-icon attributes */
                    font-size: 18px;
                    margin-right: 0;
                }}
                .content {{
                    padding: 16px;
                }}
                .metrics-grid {{
                    grid-template-columns: 1fr;
                }}
            }}

        </style>
    </head>
    <body>
        <!-- Header -->
        <header class="header">
            <div class="logo">🎓 Enterprise Command Center</div>
            <div class="nav-controls">
                <select id="roleSelector" class="role-selector">
                    <option value="executive">Executive</option>
                    <option value="technical">Technical</option>
                    <option value="analytics">Analytics</option>
                </select>
                <input type="date" id="startDatePicker" class="date-picker" value="{start_date.strftime('%Y-%m-%d')}">
                <input type="date" id="endDatePicker" class="date-picker" value="{end_date.strftime('%Y-%m-%d')}">
                <button id="refreshBtn" class="refresh-btn" onclick="refreshDashboard()">
                    <span>🔄</span> Refresh
                </button>
            </div>
        </header>

        <div class="main-container">
            <!-- Sidebar -->
            <aside class="sidebar">
                <a href="#" class="nav-item active" data-role="executive">📊 Executive</a>
                <a href="#" class="nav-item" data-role="technical">⚙️ Technical</a>
                <a href="#" class="nav-item" data-role="analytics">📈 Analytics</a>
            </aside>

            <!-- Content Area -->
            <main class="content">
                <h1 class="dashboard-title">Executive Dashboard</h1>

                <!-- Executive View -->
                <div id="executiveView" class="dashboard-view active">
                    <!-- Executive Metrics Grid -->
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">Cost Savings (USD)</div>
                            <div class="metric-value">${exec_metrics['cost_savings']:,}</div>
                            <div class="metric-change">+5.2% vs last period</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">ROI (%)</div>
                            <div class="metric-value">{exec_metrics['roi_percentage']:.2f}%</div>
                            <div class="metric-change positive">↗️ +12.3%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Total Conversations</div>
                            <div class="metric-value">{exec_metrics['total_conversations']}</div>
                            <div class="metric-change">+3.1% vs last period</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Satisfaction Score</div>
                            <div class="metric-value">{exec_metrics['satisfaction_score']:.1f}/5.0</div>
                            <div class="metric-change positive">↗️ +0.2</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Avg. Response Time (s)</div>
                            <div class="metric-value">{exec_metrics['avg_response_time']:.2f}s</div>
                            <div class="metric-change negative">↘️ -0.1s</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Automation Rate (%)</div>
                            <div class="metric-value">{exec_metrics['automation_rate']:.2f}%</div>
                            <div class="metric-change positive">↗️ +8.7%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Staff Hours Saved</div>
                            <div class="metric-value">{exec_metrics['staff_hours_saved']:.1f} hrs</div>
                            <div class="metric-change positive">↗️ +150</div>
                        </div>
                    </div>

                    <!-- Executive Charts -->
                    <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Cost Savings Trend</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{cost_savings_chart}</div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">ROI Over Time</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{roi_chart}</div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Query Volume by Intent</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{dept_volume_chart}</div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Peak Usage Hours</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{peak_hours_chart}</div>
                    </div>

                     <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Top 5 Requested Topics</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{top_topics_chart}</div>
                    </div>

                </div> <!-- End Executive View -->

                <!-- Technical View -->
                <div id="technicalView" class="dashboard-view">
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">Uptime (%)</div>
                            <div class="metric-value">{tech_metrics['uptime']:.2f}%</div>
                            <div class="metric-change">Target: {TARGET_UPTIME_PERCENT}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Avg. Response Time (ms)</div>
                            <div class="metric-value">{tech_metrics['avg_response_time']*1000:.0f}ms</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">P95 Response Time (ms)</div>
                            <div class="metric-value">{tech_metrics['p95_response_time']*1000:.0f}ms</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">P99 Response Time (ms)</div>
                            <div class="metric-value">{tech_metrics['p99_response_time']*1000:.0f}ms</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Error Rate (%)</div>
                            <div class="metric-value">{tech_metrics['error_rate']:.2f}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Active Sessions</div>
                            <div class="metric-value">{tech_metrics['active_sessions']}</div>
                        </div>
                    </div>

                     <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Response Time Trends (Avg, P95, P99)</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{response_time_trend_chart}</div>
                    </div>

                    <div class="table-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Recent Errors</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">Export</button>
                            </div>
                        </div>
                        {error_log_html}
                    </div>

                </div> <!-- End Technical View -->

                <!-- Analytics View -->
                <div id="analyticsView" class="dashboard-view">
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">Total Conversations</div>
                            <div class="metric-value">{analytics_metrics['total_conversations']}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Unique Users</div>
                            <div class="metric-value">{analytics_metrics['unique_users']}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Avg. Conversation Length</div>
                            <div class="metric-value">{analytics_metrics['avg_conversation_length']:.1f} msg</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Intent Distribution</div>
                            <div class="metric-value">See Chart</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Sentiment Distribution</div>
                            <div class="metric-value">See Chart</div>
                        </div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Sentiment Trend Over Time</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{sentiment_trend_chart}</div>
                    </div>

                     <div class="chart-card">
                        <div class="chart-header">
                            <h2 class="chart-title">Query Volume by Intent</h2>
                            <div class="chart-actions">
                                <button class="chart-btn">PNG</button>
                                <button class="chart-btn">CSV</button>
                            </div>
                        </div>
                        <div class="chart-container">{dept_volume_chart}</div>
                    </div>

                </div> <!-- End Analytics View -->

            </main>
        </div>

        <script>
            // Function to switch between dashboard views
            function switchView(role) {{
                // Hide all views
                document.querySelectorAll('.dashboard-view').forEach(view => view.classList.remove('active'));
                // Remove active class from nav items
                document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
                // Show selected view
                document.getElementById(role + 'View').classList.add('active');
                // Update title
                document.querySelector('.dashboard-title').textContent = role.charAt(0).toUpperCase() + role.slice(1) + ' Dashboard';
                // Update active nav item
                document.querySelector(`.nav-item[data-role="${{role}}"]`).classList.add('active');
                // Update role selector
                document.getElementById('roleSelector').value = role;
            }}

            // Event listeners for sidebar navigation
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.addEventListener('click', (e) => {{
                    e.preventDefault();
                    const role = item.getAttribute('data-role');
                    switchView(role);
                }});
            }});

            // Event listener for role selector dropdown
            document.getElementById('roleSelector').addEventListener('change', (e) => {{
                const selectedRole = e.target.value;
                switchView(selectedRole);
            }});

            // Refresh dashboard function (placeholder for now, could trigger data reload via fetch)
            function refreshDashboard() {{
                const refreshBtn = document.getElementById('refreshBtn');
                refreshBtn.innerHTML = '<span>⏳</span> Loading...';
                refreshBtn.disabled = true;

                // Simulate a delay to mimic loading
                setTimeout(() => {{
                     location.reload(); // Reload the page to fetch fresh data
                     // In a real impl, you'd fetch new data and update the DOM/chart HTML
                }}, 1000);
            }}

            // Initialize with Executive view
            // switchView('executive'); // Already active by default in HTML

        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Simple health check for the dashboard service."""
    return {"status": "ok", "service": "dashboard", "timestamp": datetime.now(timezone.utc).isoformat()}

# --- Main Execution Block (for running with uvicorn) ---
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001) # Run on port 8001 to avoid conflict with bot on 8000/8080