"""
🚀 Enterprise Command Center: College Bot Analytics Dashboard
===============================================================
Real-time, interactive, and visually stunning dashboard powered by FastAPI and Plotly.
Monitors bot performance, user engagement, sentiment, and operational health.
"""

import logging
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client as SupabaseClient
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta, timezone
import json
from typing import Dict, List, Optional
import secrets # For session management if needed
from pydantic import BaseModel # For request/response models if needed

# Import configuration
from bot.config import SUPABASE_URL, SUPABASE_KEY, ENVIRONMENT, PORT

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO if ENVIRONMENT != "development" else logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Global Variables for Supabase Client ---
supabase: Optional[SupabaseClient] = None

# --- Application Lifecycle Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown tasks for the dashboard.
    """
    global supabase
    logger.info("🚀 Starting up College Bot Analytics Dashboard...")

    # Initialize Supabase Client for data fetching
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Connected to Supabase for dashboard data.")
    except Exception as e:
        logger.critical(f"❌ Failed to connect to Supabase for dashboard: {e}")
        raise e

    yield # Hand over control to the application

    # Shutdown tasks
    logger.info("🛑 Shutting down College Bot Analytics Dashboard...")

# --- Initialize FastAPI App ---
app = FastAPI(
    title="College Bot Analytics Dashboard",
    description="Enterprise-grade analytics dashboard for monitoring the college WhatsApp bot.",
    version="2.0.0",
    lifespan=lifespan
)

# --- Templates and Static Files (Optional, for custom HTML/CSS/JS) ---
# If you want to serve custom HTML/CSS/JS for advanced frontend, use these.
# For now, we'll serve the main dashboard page via a template.
templates = Jinja2Templates(directory="dashboard/templates") # Create 'templates' folder if using
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static") # Create 'static' folder if using

# --- Pydantic Models for API Endpoints (Optional) ---
class DashboardMetrics(BaseModel):
    total_interactions: int
    avg_response_time: float
    positive_sentiment_rate: float
    escalated_conversations: int

# --- Data Fetching Helper Functions ---
async def fetch_conversation_metrics_async(start_date: datetime, end_date: datetime) -> Dict:
    """Fetches core conversation metrics from Supabase."""
    # Example query - adjust table and column names based on your schema
    query = supabase.table("conversations") \
        .select("id, timestamp, sentiment, response_time, intent, urgency") \
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
        avg_response_time = df['response_time'].mean() if 'response_time' in df.columns else 0.0
        positive_count = df[df['sentiment'] == 'positive'].shape[0]
        negative_count = df[df['sentiment'] == 'negative'].shape[0]
        very_negative_count = df[df['sentiment'] == 'very_negative'].shape[0]
        total_sentiment_count = positive_count + negative_count + very_negative_count
        positive_sentiment_rate = (positive_count / total_sentiment_count * 100) if total_sentiment_count > 0 else 0.0
        escalated_conversations = df[df['urgency'] == 'critical'].shape[0] + df[df['sentiment'] == 'very_negative'].shape[0]

        # Intent Distribution
        intent_counts = df['intent'].value_counts().to_dict() if 'intent' in df.columns else {}

        # Sentiment Over Time (Daily Aggregation)
        daily_sentiment = df.groupby('date')['sentiment'].value_counts().unstack(fill_value=0).reset_index()
        daily_sentiment['date_str'] = daily_sentiment['date'].astype(str)
        sentiment_over_time = daily_sentiment.to_dict(orient='records')

        return {
            "total_interactions": total_interactions,
            "avg_response_time": round(avg_response_time, 2),
            "positive_sentiment_rate": round(positive_sentiment_rate, 2),
            "escalated_conversations": escalated_conversations,
            "intent_distribution": intent_counts,
            "sentiment_over_time": sentiment_over_time
        }
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
        # Query for last interaction
        last_interaction_query = supabase.table("conversations").select("*").order("timestamp", desc=True).limit(1).execute()
        last_interaction = last_interaction_query.data[0] if last_interaction_query.data else None
        last_interaction_time = last_interaction['timestamp'] if last_interaction else "Never"

        # Example: Count recent errors (assuming an 'errors' table exists or errors are logged in 'conversations')
        # This requires a specific error logging strategy in your main bot.
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
def create_interaction_volume_chart(data: List[Dict]) -> str:
    """Creates an interactive line chart for interaction volume over time."""
    if not data or all(len(day_data.get(f, [])) == 0 for f in ['positive', 'negative', 'very_negative'] for day_data in data):
         # Fallback chart if no sentiment data
        dates = [d['date_str'] for d in data]
        total_counts = [sum([d.get(k, 0) for k in ['positive', 'negative', 'very_negative']]) for d in data]
        fig = px.line(x=dates, y=total_counts, title="Total Interactions Over Time")
    else:
        # Assuming data is structured as [{'date_str': 'YYYY-MM-DD', 'positive': 5, 'negative': 2, ...}, ...]
        df = pd.DataFrame(data)
        df_melted = df.melt(id_vars=['date_str'], value_vars=['positive', 'negative', 'very_negative'], var_name='sentiment', value_name='count')
        fig = px.line(df_melted, x='date_str', y='count', color='sentiment', title="Interaction Volume by Sentiment Over Time")

    fig.update_layout(
        template="plotly_dark", # Dark theme for a modern look
        paper_bgcolor='rgba(0,0,0,0)', # Transparent background
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        title_font_size=20,
        hovermode='x unified'
    )
    return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False})

def create_intent_pie_chart(intent_counts: Dict[str, int]) -> str:
    """Creates a pie chart for intent distribution."""
    if not intent_counts:
        fig = go.Figure(data=[go.Pie(labels=['No Data'], values=[1])])
        fig.update_layout(title="Intent Distribution (No Data)", template="plotly_dark")
    else:
        fig = px.pie(values=list(intent_counts.values()), names=list(intent_counts.keys()), title="Query Intent Distribution")
        fig.update_layout(template="plotly_dark", font=dict(color="white"))

    return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False})

def create_sentiment_gauge(positive_rate: float) -> str:
    """Creates a gauge chart for positive sentiment rate."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = positive_rate,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Positive Sentiment Rate (%)"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkgreen"}, # Color of the needle
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'lightcoral'},
                {'range': [50, 75], 'color': 'khaki'},
                {'range': [75, 100], 'color': 'lightgreen'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80}})) # Threshold line at 80%

    fig.update_layout(template="plotly_dark", font=dict(color="white", size=16))
    return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False})

# --- FastAPI Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Renders the main dashboard page."""
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

    # Render HTML page (using Jinja2 template or returning raw HTML)
    # For simplicity, returning raw HTML here. A template engine is better for complex layouts.
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>College Bot Command Center</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #121212; color: white; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .metric-card {{ background-color: #1e1e1e; padding: 20px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
            .metric-label {{ font-size: 0.9em; color: #aaaaaa; }}
            .status-indicator {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
            .status-operational {{ background-color: #4CAF50; }}
            .status-warning {{ background-color: #FFC107; }}
            .status-error {{ background-color: #F44336; }}
            .chart-container {{ margin-bottom: 30px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #aaaaaa; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 College Bot Command Center</h1>
                <p>Real-Time Analytics & Performance Monitoring</p>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics['total_interactions']}</div>
                    <div class="metric-label">Total Interactions (7d)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['avg_response_time']}s</div>
                    <div class="metric-label">Avg. Response Time</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['positive_sentiment_rate']}%</div>
                    <div class="metric-label">Positive Sentiment</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['escalated_conversations']}</div>
                    <div class="metric-label">Escalated Cases</div>
                </div>
            </div>

            <div class="metrics-grid">
                 <div class="metric-card">
                    <span class="status-indicator status-{status['system_status'].lower().replace(' ', '-')}"></span>
                    <div class="metric-value">{status['system_status']}</div>
                    <div class="metric-label">System Status</div>
                </div>
                 <div class="metric-card">
                    <div class="metric-value">{status['last_interaction']}</div>
                    <div class="metric-label">Last Interaction</div>
                </div>
            </div>

            <div class="chart-container">
                {volume_chart_html}
            </div>
            <div class="chart-container">
                {intent_chart_html}
            </div>
             <div class="chart-container">
                {sentiment_gauge_html}
            </div>

            <div class="footer">
                <p>Enterprise Dashboard v2.0 | Data refreshed every 30 seconds</p>
            </div>
        </div>
        <script>
            // Optional: Auto-refresh the page every 30 seconds
            // setTimeout(function(){ location.reload(); }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/metrics", response_model=DashboardMetrics)
async def get_metrics_api():
    """API endpoint to fetch raw metrics data."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=1) # Last 24 hours
    metrics = await fetch_conversation_metrics_async(start_date, end_date)
    return JSONResponse(content=metrics)

@app.get("/health")
async def health_check():
    """Simple health check for the dashboard service."""
    return {"status": "ok", "service": "dashboard", "timestamp": datetime.now(timezone.utc).isoformat()}

# --- Main Execution Block (for running with uvicorn) ---
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001) # Run on port 8001 to avoid conflict with bot on 8000