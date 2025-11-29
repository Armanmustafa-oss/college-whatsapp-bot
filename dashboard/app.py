"""
🚀 Spotify-Style Analytics Dashboard for College WhatsApp Bot
===============================================================

A modern, dark-themed dashboard powered by FastAPI and Plotly.
Focuses on key metrics, interactive charts, and a clean user experience.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta, timezone
import json
from typing import Dict, List, Optional, TYPE_CHECKING
import numpy as np # For handling NaN values

# Import configuration (adjust import path if necessary)
from bot.config import SUPABASE_URL, SUPABASE_KEY, ENVIRONMENT, PORT

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO if ENVIRONMENT != "development" else logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Global Variables for Supabase Client ---
if TYPE_CHECKING:
    from supabase import Client as SupabaseClient

supabase: Optional['SupabaseClient'] = None

# --- Application Lifecycle Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown tasks for the dashboard.
    """
    global supabase
    logger.info("🚀 Starting up Spotify-Style College Bot Dashboard...")

    # Initialize Supabase Client for data fetching
    try:
        from supabase import create_client, Client as SupabaseClient
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Connected to Supabase for dashboard data.")
    except Exception as e:
        logger.critical(f"❌ Failed to connect to Supabase for dashboard: {e}")
        supabase = None # Allow app to start, but metrics will be empty

    yield # Hand over control to the application

    # Shutdown tasks
    logger.info("🛑 Shutting down Spotify-Style College Bot Dashboard...")

# --- Initialize FastAPI App ---
app = FastAPI(
    title="Spotify-Style College Bot Dashboard",
    description="Modern analytics dashboard for monitoring the college WhatsApp bot.",
    version="3.0.0",
    lifespan=lifespan
)

# --- Data Fetching Helper Functions ---
async def fetch_conversation_metrics_async(start_date: datetime, end_date: datetime) -> Dict:
    """Fetches core conversation metrics from Supabase, handling NaN values."""
    # Example query - adjust table and column names based on your schema
    query = supabase.table("conversations") \
        .select("id, timestamp, sentiment, response_time_seconds, intent, urgency") \
        .gte("timestamp", start_date.isoformat()) \
        .lte("timestamp", end_date.isoformat())

    try:
        response = query.execute()
        data = response.data
        df = pd.DataFrame(data)
        if df.empty:
            return {
                "total_interactions": 0,
                "avg_response_time": 0.0,
                "positive_sentiment_rate": 0.0,
                "escalated_conversations": 0,
                "intent_distribution": {},
                "sentiment_over_time": []
            }

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date

        total_interactions = len(df)
        # Calculate average response time, handle potential NaN if no valid times
        avg_response_time_raw = df['response_time_seconds'].mean()
        avg_response_time = float(avg_response_time_raw) if pd.notna(avg_response_time_raw) else 0.0

        positive_count = df[df['sentiment'] == 'positive'].shape[0]
        negative_count = df[df['sentiment'] == 'negative'].shape[0]
        very_negative_count = df[df['sentiment'] == 'very_negative'].shape[0]
        total_sentiment_count = positive_count + negative_count + very_negative_count
        if total_sentiment_count > 0:
            positive_sentiment_rate_raw = (positive_count / total_sentiment_count * 100)
            positive_sentiment_rate = float(positive_sentiment_rate_raw) if pd.notna(positive_sentiment_rate_raw) else 0.0
        else:
            positive_sentiment_rate = 0.0

        escalated_conversations = df[df['urgency'] == 'critical'].shape[0] + df[df['sentiment'] == 'very_negative'].shape[0]

        # Intent Distribution - handle potential NaN counts if intents are missing
        intent_counts_raw = df['intent'].value_counts().to_dict() if 'intent' in df.columns else {}
        intent_counts = {k: int(v) for k, v in intent_counts_raw.items() if pd.notna(k) and pd.notna(v)}

        # Sentiment Over Time (Daily Aggregation) - handle potential NaN in counts
        daily_sentiment_raw = df.groupby('date')['sentiment'].value_counts().unstack(fill_value=0).reset_index()
        daily_sentiment_raw['date_str'] = daily_sentiment_raw['date'].astype(str)
        # Replace any remaining NaN in count columns with 0 before converting to dict
        count_columns = [col for col in daily_sentiment_raw.columns if col not in ('date', 'date_str')]
        daily_sentiment_raw[count_columns] = daily_sentiment_raw[count_columns].fillna(0)
        sentiment_over_time = daily_sentiment_raw.to_dict(orient='records')

        # Ensure all numeric values are JSON serializable (no NaN, inf, -inf)
        result = {
            "total_interactions": int(total_interactions),
            "avg_response_time": round(avg_response_time, 2),
            "positive_sentiment_rate": round(positive_sentiment_rate, 2),
            "escalated_conversations": int(escalated_conversations),
            "intent_distribution": intent_counts,
            "sentiment_over_time": sentiment_over_time
        }

        # Replace any remaining NaN/inf values in the final dictionary with None/0
        def replace_nan_inf(obj):
            if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
                return 0 # Or None, depending on preference for display
            elif isinstance(obj, dict):
                return {k: replace_nan_inf(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_nan_inf(item) for item in obj]
            else:
                return obj

        return replace_nan_inf(result)

    except Exception as e:
        logger.error(f"Error fetching conversation metrics: {e}")
        return {
            "total_interactions": 0,
            "avg_response_time": 0.0,
            "positive_sentiment_rate": 0.0,
            "escalated_conversations": 0,
            "intent_distribution": {},
            "sentiment_over_time": []
        }

async def fetch_real_time_status_async() -> Dict:
    """Fetches real-time status indicators."""
    # Example: Check last interaction time, active sessions (if tracked), error counts
    try:
        if not supabase:
             return {
                "last_interaction": "Error (No Supabase)",
                "system_status": "Error",
                "active_sessions": 0,
                "recent_errors": -1
            }
        # Query for last interaction
        last_interaction_query = supabase.table("conversations").select("*").order("timestamp", desc=True).limit(1).execute()
        last_interaction = last_interaction_query.data[0] if last_interaction_query.data else None
        last_interaction_time = last_interaction['timestamp'] if last_interaction else "Never"

        # Example: Count recent errors (assuming an 'errors' table exists or errors are logged in 'conversations')
        # For now, let's assume a simple status based on last interaction recency.
        current_time = datetime.now(timezone.utc)
        if last_interaction_time != "Never":
            last_time_dt = datetime.fromisoformat(last_interaction_time.replace('Z', '+00:00'))
            time_since_last = (current_time - last_time_dt).total_seconds()
            status = "Operational" if time_since_last < 300 else "Warning" # Operational if last interaction < 5 mins
        else:
            status = "No Data"

        return {
            "last_interaction": last_interaction_time,
            "system_status": status,
            "active_sessions": 0, # Placeholder - requires session tracking in main bot
            "recent_errors": 0 # Placeholder - requires error logging
        }
    except Exception as e:
        logger.error(f"Error fetching real-time status: {e}")
        return {
            "last_interaction": "Error",
            "system_status": "Error",
            "active_sessions": 0,
            "recent_errors": -1
        }

# --- Chart Generation Functions ---
def create_interaction_volume_chart(sentiment_over_time: List[Dict]) -> str:
    """Creates an interactive line chart for interaction volume over time."""
    if not sentiment_over_time:
        fig = px.line(title="Interaction Volume Over Time (No Data)")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            hovermode='x unified'
        )
        return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

    # Convert to DataFrame
    df = pd.DataFrame(sentiment_over_time)
    # Melt the DataFrame to get sentiment as a category
    date_col = 'date_str'
    sentiment_cols = [col for col in df.columns if col not in (date_col, 'date')]
    if not sentiment_cols:
        fig = px.line(title="Interaction Volume Over Time (No Sentiment Data)")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            title_font_size=16,
            hovermode='x unified'
        )
        return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

    df_melted = df.melt(id_vars=[date_col], value_vars=sentiment_cols, var_name='sentiment', value_name='count')

    fig = px.line(df_melted, x=date_col, y='count', color='sentiment', title="Interaction Volume by Sentiment Over Time")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        title_font_size=16,
        hovermode='x unified'
    )
    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_intent_pie_chart(intent_counts: Dict[str, int]) -> str:
    """Creates a pie chart for intent distribution."""
    if not intent_counts:
        fig = go.Figure(data=[go.Pie(labels=['No Data'], values=[1])])
        fig.update_layout(title="Query Intent Distribution (No Data)", template="plotly_dark", font=dict(color="white"))
    else:
        # Sort intents by count descending for better visual hierarchy
        sorted_items = sorted(intent_counts.items(), key=lambda item: item[1], reverse=True)
        sorted_names, sorted_values = zip(*sorted_items) if sorted_items else ([], [])
        fig = px.pie(values=sorted_values, names=sorted_names, title="Query Intent Distribution")
        fig.update_layout(template="plotly_dark", font=dict(color="white"))

    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

def create_sentiment_gauge(positive_rate: float) -> str:
    """Creates a gauge chart for positive sentiment rate."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = positive_rate,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Positive Sentiment Rate (%)"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#1DB954"}, # Spotify Green
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "rgba(255,255,255,0.2)",
            'steps': [
                {'range': [0, 50], 'color': '#FF4136'}, # Red
                {'range': [50, 75], 'color': '#FFDC00'}, # Yellow
                {'range': [75, 100], 'color': '#2ECC40'}], # Green
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 80}}))

    fig.update_layout(template="plotly_dark", font=dict(color="white", size=16))
    return fig.to_html(include_plotlyjs=False, config={'displayModeBar': False})

# --- FastAPI Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Renders the main Spotify-style dashboard page."""
    # Fetch data for the dashboard (last 7 days by default)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)

    metrics_task = fetch_conversation_metrics_async(start_date, end_date)
    status_task = fetch_real_time_status_async()

    metrics, status = await asyncio.gather(metrics_task, status_task)

    # Generate charts
    volume_chart_html = create_interaction_volume_chart(metrics.get("sentiment_over_time", []))
    intent_chart_html = create_intent_pie_chart(metrics.get("intent_distribution", {}))
    sentiment_gauge_html = create_sentiment_gauge(metrics.get("positive_sentiment_rate", 0))

    # --- Spotify-Style HTML Template ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>College Bot Command Center</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            :root {{
                --sp-black: #121212;
                --sp-dark-gray: #181818;
                --sp-gray: #282828;
                --sp-light-gray: #B3B3B3;
                --sp-white: #FFFFFF;
                --sp-green: #1DB954;
                --sp-accent: #BB86FC; /* Could be another color */
                --card-bg: var(--sp-gray);
                --text-primary: var(--sp-white);
                --text-secondary: var(--sp-light-gray);
            }}

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}

            body {{
                background-color: var(--sp-black);
                color: var(--text-primary);
                display: flex;
                min-height: 100vh;
            }}

            /* Sidebar */
            .sidebar {{
                width: 220px;
                background-color: var(--sp-black);
                padding: 24px 12px;
                position: fixed;
                height: 100vh;
                overflow-y: auto;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }}

            .logo {{
                color: var(--sp-green);
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 24px;
                padding-left: 12px;
            }}

            .nav-item {{
                color: var(--text-secondary);
                text-decoration: none;
                display: block;
                padding: 10px 16px;
                border-radius: 4px;
                margin-bottom: 4px;
                transition: background-color 0.2s ease;
                font-size: 14px;
            }}

            .nav-item:hover {{
                background-color: var(--sp-gray);
                color: var(--text-primary);
            }}

            /* Main Content */
            .main-content {{
                flex: 1;
                margin-left: 220px; /* Match sidebar width */
                padding: 32px 48px;
            }}

            .header {{
                margin-bottom: 32px;
            }}

            .header h1 {{
                font-size: 28px;
                font-weight: 700;
            }}

            .header p {{
                color: var(--text-secondary);
                margin-top: 8px;
            }}

            /* Grid Layout for Metrics and Charts */
            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 24px;
                margin-bottom: 32px;
            }}

            /* Metric Card */
            .metric-card {{
                background-color: var(--card-bg);
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}

            .metric-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
            }}

            .metric-card h3 {{
                color: var(--text-secondary);
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }}

            .metric-value {{
                font-size: 32px;
                font-weight: 700;
                color: var(--text-primary);
            }}

            /* Chart Card */
            .chart-card {{
                background-color: var(--card-bg);
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 24px;
            }}

            .chart-card h2 {{
                color: var(--text-primary);
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 16px;
            }}

            .chart-container {{
                width: 100%;
            }}

            /* Responsive Adjustments */
            @media (max-width: 768px) {{
                .sidebar {{
                    width: 60px;
                    align-items: center;
                }}
                .logo, .nav-item span {{
                    display: none;
                }}
                .logo-icon {{
                    display: block;
                    font-size: 24px;
                }}
                .main-content {{
                    margin-left: 60px;
                }}
                .dashboard-grid {{
                    grid-template-columns: 1fr;
                }}
            }}

        </style>
    </head>
    <body>
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="logo">🎵 BotCommand</div>
            <a href="#" class="nav-item">Overview</a>
            <a href="#" class="nav-item">Analytics</a>
            <a href="#" class="nav-item">Performance</a>
            <a href="#" class="nav-item">Users</a>
            <a href="#" class="nav-item">Settings</a>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <h1>Dashboard Overview</h1>
                <p>Real-time metrics and analytics for your college WhatsApp bot.</p>
            </div>

            <!-- Metric Cards Grid -->
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>Total Interactions (7d)</h3>
                    <div class="metric-value">{metrics['total_interactions']}</div>
                </div>
                <div class="metric-card">
                    <h3>Avg. Response Time</h3>
                    <div class="metric-value">{metrics['avg_response_time']}s</div>
                </div>
                <div class="metric-card">
                    <h3>Positive Sentiment</h3>
                    <div class="metric-value">{metrics['positive_sentiment_rate']}%</div>
                </div>
                <div class="metric-card">
                    <h3>Escalated Cases</h3>
                    <div class="metric-value">{metrics['escalated_conversations']}</div>
                </div>
            </div>

            <!-- Charts -->
            <div class="chart-card">
                <h2>Interaction Volume Over Time</h2>
                <div class="chart-container">{volume_chart_html}</div>
            </div>

            <div class="chart-card">
                <h2>Query Intent Distribution</h2>
                <div class="chart-container">{intent_chart_html}</div>
            </div>

            <div class="chart-card">
                <h2>Positive Sentiment Gauge</h2>
                <div class="chart-container">{sentiment_gauge_html}</div>
            </div>

            <!-- Status Card (Example) -->
            <div class="chart-card">
                <h2>System Status</h2>
                <p><strong>Last Interaction:</strong> {status['last_interaction']}</p>
                <p><strong>System Status:</strong> <span style="color: {'#1DB954' if status['system_status'] == 'Operational' else '#FF4136'}">{status['system_status']}</span></p>
                <p><strong>Active Sessions:</strong> {status['active_sessions']}</p>
            </div>

        </div>
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