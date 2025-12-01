"""
College-Bot Analytics Dashboard
A production-ready analytics dashboard built with FastAPI and Plotly
Integrates with Supabase PostgreSQL database
Single-file application for seamless Railway deployment
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from functools import lru_cache

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
import logging

# ============================================================================
# CONFIGURATION
# ============================================================================

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Validate configuration
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")

# Logging setup
logging.basicConfig(level=logging.INFO if DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="College-Bot Analytics Dashboard",
    description="Interactive analytics dashboard for WhatsApp bot conversations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SUPABASE CLIENT
# ============================================================================

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get Supabase client instance (cached)"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

def fetch_conversations_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """
    Fetch conversation data from Supabase
    
    Args:
        start_date: ISO format date string (YYYY-MM-DD)
        end_date: ISO format date string (YYYY-MM-DD)
    
    Returns:
        List of conversation records
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("conversations").select("*")
        
        # Apply date filters if provided
        if start_date:
            query = query.gte("created_at", f"{start_date}T00:00:00")
        if end_date:
            query = query.lte("created_at", f"{end_date}T23:59:59")
        
        response = query.order("created_at", desc=True).limit(1000).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        return []

def calculate_metrics(conversations: List[Dict]) -> Dict[str, Any]:
    """
    Calculate key metrics from conversation data
    
    Args:
        conversations: List of conversation records
    
    Returns:
        Dictionary with calculated metrics
    """
    if not conversations:
        return {
            "total_conversations": 0,
            "avg_response_time": 0,
            "positive_sentiment_rate": 0,
            "escalated_conversations": 0,
            "avg_satisfaction": 0,
        }
    
    total = len(conversations)
    
    # Calculate response time (in seconds)
    response_times = []
    for conv in conversations:
        if conv.get("response_time"):
            response_times.append(conv["response_time"])
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Calculate sentiment rate
    positive_count = sum(1 for conv in conversations if conv.get("sentiment") == "positive")
    positive_rate = (positive_count / total * 100) if total > 0 else 0
    
    # Calculate escalation rate
    escalated_count = sum(1 for conv in conversations if conv.get("escalated", False))
    
    # Calculate average satisfaction
    satisfaction_scores = [conv.get("satisfaction_score", 0) for conv in conversations if conv.get("satisfaction_score")]
    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
    
    return {
        "total_conversations": total,
        "avg_response_time": round(avg_response_time, 2),
        "positive_sentiment_rate": round(positive_rate, 1),
        "escalated_conversations": escalated_count,
        "avg_satisfaction": round(avg_satisfaction, 1),
    }

# ============================================================================
# CHART GENERATION FUNCTIONS
# ============================================================================

def generate_conversation_volume_chart(conversations: List[Dict]) -> str:
    """Generate conversation volume over time (Line chart)"""
    if not conversations:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig.to_html(include_plotlyjs=False, div_id="chart_volume")
    
    # Group conversations by date
    date_counts = {}
    for conv in conversations:
        if conv.get("created_at"):
            date = conv["created_at"][:10]  # Extract YYYY-MM-DD
            date_counts[date] = date_counts.get(date, 0) + 1
    
    dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in dates]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=counts,
        mode='lines+markers',
        name='Conversations',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
    ))
    
    fig.update_layout(
        title="Conversation Volume Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Conversations",
        hovermode='x unified',
        template="plotly_dark",
        plot_bgcolor='rgba(15, 20, 25, 0.5)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=400,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_volume")

def generate_sentiment_distribution_chart(conversations: List[Dict]) -> str:
    """Generate sentiment distribution (Pie chart)"""
    if not conversations:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig.to_html(include_plotlyjs=False, div_id="chart_sentiment")
    
    # Count sentiments
    sentiment_counts = {}
    for conv in conversations:
        sentiment = conv.get("sentiment", "neutral")
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    labels = list(sentiment_counts.keys())
    values = list(sentiment_counts.values())
    colors = {
        "positive": "#10b981",
        "neutral": "#6b7280",
        "negative": "#ef4444"
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=[colors.get(label, "#3b82f6") for label in labels]),
        textposition='inside',
        textinfo='percent+label',
    )])
    
    fig.update_layout(
        title="Sentiment Distribution",
        template="plotly_dark",
        plot_bgcolor='rgba(15, 20, 25, 0.5)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=400,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_sentiment")

def generate_response_time_chart(conversations: List[Dict]) -> str:
    """Generate response time distribution (Bar chart)"""
    if not conversations:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig.to_html(include_plotlyjs=False, div_id="chart_response")
    
    # Create response time buckets
    response_times = [conv.get("response_time", 0) for conv in conversations if conv.get("response_time")]
    
    if not response_times:
        fig = go.Figure()
        fig.add_annotation(text="No response time data available", showarrow=False)
        return fig.to_html(include_plotlyjs=False, div_id="chart_response")
    
    # Create histogram
    fig = go.Figure(data=[go.Histogram(
        x=response_times,
        nbinsx=20,
        marker=dict(color='#8b5cf6'),
        name='Response Time (seconds)',
    )])
    
    fig.update_layout(
        title="Response Time Distribution",
        xaxis_title="Response Time (seconds)",
        yaxis_title="Frequency",
        template="plotly_dark",
        plot_bgcolor='rgba(15, 20, 25, 0.5)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=400,
        showlegend=False,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_response")

def generate_intent_distribution_chart(conversations: List[Dict]) -> str:
    """Generate intent distribution (Bar chart)"""
    if not conversations:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False)
        return fig.to_html(include_plotlyjs=False, div_id="chart_intent")
    
    # Count intents
    intent_counts = {}
    for conv in conversations:
        intent = conv.get("intent", "unknown")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    # Sort by count and take top 10
    top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    labels = [item[0] for item in top_intents]
    values = [item[1] for item in top_intents]
    
    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker=dict(color='#06b6d4'),
        text=values,
        textposition='outside',
    )])
    
    fig.update_layout(
        title="Top 10 Query Intents",
        xaxis_title="Intent",
        yaxis_title="Count",
        template="plotly_dark",
        plot_bgcolor='rgba(15, 20, 25, 0.5)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=400,
        xaxis_tickangle=-45,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_intent")

def generate_satisfaction_gauge_chart(avg_satisfaction: float) -> str:
    """Generate satisfaction gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_satisfaction,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Average Satisfaction"},
        delta={'reference': 80},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#3b82f6"},
            'steps': [
                {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.2)"},
                {'range': [50, 80], 'color': "rgba(251, 146, 60, 0.2)"},
                {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.2)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(15, 20, 25, 0.5)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=400,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_satisfaction")

# ============================================================================
# HTML TEMPLATE
# ============================================================================

def generate_html_template(
    metrics: Dict[str, Any],
    chart_volume: str,
    chart_sentiment: str,
    chart_response: str,
    chart_intent: str,
    chart_satisfaction: str,
    start_date: str,
    end_date: str,
) -> str:
    """Generate complete HTML page with embedded charts"""
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>College-Bot Analytics Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
                color: #e5e7eb;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            header {{
                background: linear-gradient(135deg, rgba(26, 31, 46, 0.8) 0%, rgba(15, 20, 25, 0.8) 100%);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 30px;
                backdrop-filter: blur(10px);
            }}
            
            h1 {{
                background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 700;
            }}
            
            .subtitle {{
                color: #9ca3af;
                font-size: 1.1em;
            }}
            
            .filter-section {{
                background: rgba(26, 31, 46, 0.6);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
                display: flex;
                gap: 15px;
                align-items: flex-end;
                flex-wrap: wrap;
            }}
            
            .filter-group {{
                display: flex;
                flex-direction: column;
                gap: 5px;
            }}
            
            .filter-group label {{
                font-size: 0.9em;
                color: #9ca3af;
                font-weight: 500;
            }}
            
            .filter-group input {{
                padding: 10px 12px;
                background: rgba(15, 20, 25, 0.8);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 6px;
                color: #e5e7eb;
                font-size: 0.95em;
                transition: all 0.3s ease;
            }}
            
            .filter-group input:focus {{
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }}
            
            button {{
                padding: 10px 24px;
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.95em;
            }}
            
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
            }}
            
            button:active {{
                transform: translateY(0);
            }}
            
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, rgba(26, 31, 46, 0.8) 0%, rgba(15, 20, 25, 0.8) 100%);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 25px;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }}
            
            .metric-card:hover {{
                border-color: rgba(59, 130, 246, 0.5);
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(59, 130, 246, 0.1);
            }}
            
            .metric-label {{
                color: #9ca3af;
                font-size: 0.9em;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .metric-value {{
                font-size: 2.2em;
                font-weight: 700;
                background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .chart-card {{
                background: linear-gradient(135deg, rgba(26, 31, 46, 0.8) 0%, rgba(15, 20, 25, 0.8) 100%);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 20px;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }}
            
            .chart-card:hover {{
                border-color: rgba(59, 130, 246, 0.5);
                box-shadow: 0 10px 30px rgba(59, 130, 246, 0.1);
            }}
            
            .chart-card h3 {{
                color: #e5e7eb;
                margin-bottom: 15px;
                font-size: 1.2em;
            }}
            
            footer {{
                text-align: center;
                color: #6b7280;
                font-size: 0.9em;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid rgba(59, 130, 246, 0.1);
            }}
            
            .loading {{
                text-align: center;
                padding: 40px;
                color: #9ca3af;
            }}
            
            @media (max-width: 768px) {{
                h1 {{
                    font-size: 1.8em;
                }}
                
                .charts-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .filter-section {{
                    flex-direction: column;
                    align-items: stretch;
                }}
                
                .filter-group input {{
                    width: 100%;
                }}
                
                button {{
                    width: 100%;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>College-Bot Analytics</h1>
                <p class="subtitle">WhatsApp Bot Performance Dashboard</p>
            </header>
            
            <div class="filter-section">
                <div class="filter-group">
                    <label for="start_date">Start Date</label>
                    <input type="date" id="start_date" value="{start_date}">
                </div>
                <div class="filter-group">
                    <label for="end_date">End Date</label>
                    <input type="date" id="end_date" value="{end_date}">
                </div>
                <button onclick="applyFilters()">Apply Filters</button>
                <button onclick="resetFilters()" style="background: rgba(59, 130, 246, 0.2); color: #3b82f6;">Reset</button>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Conversations</div>
                    <div class="metric-value">{metrics['total_conversations']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value">{metrics['avg_response_time']}s</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Positive Sentiment</div>
                    <div class="metric-value">{metrics['positive_sentiment_rate']}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Escalated Cases</div>
                    <div class="metric-value">{metrics['escalated_conversations']}</div>
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="chart-card">
                    {chart_volume}
                </div>
                <div class="chart-card">
                    {chart_sentiment}
                </div>
                <div class="chart-card">
                    {chart_response}
                </div>
                <div class="chart-card">
                    {chart_intent}
                </div>
                <div class="chart-card">
                    {chart_satisfaction}
                </div>
            </div>
            
            <footer>
                <p>College-Bot Analytics Dashboard • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </footer>
        </div>
        
        <script>
            function applyFilters() {{
                const startDate = document.getElementById('start_date').value;
                const endDate = document.getElementById('end_date').value;
                
                if (!startDate || !endDate) {{
                    alert('Please select both start and end dates');
                    return;
                }}
                
                window.location.href = `/?start_date=${{startDate}}&end_date=${{endDate}}`;
            }}
            
            function resetFilters() {{
                window.location.href = '/';
            }}
        </script>
    </body>
    </html>
    """

# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Main dashboard page with interactive charts
    
    Query Parameters:
        start_date: Optional start date for filtering (YYYY-MM-DD)
        end_date: Optional end date for filtering (YYYY-MM-DD)
    """
    try:
        # Set default date range (last 30 days)
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Fetch data
        conversations = fetch_conversations_data(start_date, end_date)
        
        # Calculate metrics
        metrics = calculate_metrics(conversations)
        
        # Generate charts
        chart_volume = generate_conversation_volume_chart(conversations)
        chart_sentiment = generate_sentiment_distribution_chart(conversations)
        chart_response = generate_response_time_chart(conversations)
        chart_intent = generate_intent_distribution_chart(conversations)
        chart_satisfaction = generate_satisfaction_gauge_chart(metrics["avg_satisfaction"])
        
        # Generate HTML
        html = generate_html_template(
            metrics=metrics,
            chart_volume=chart_volume,
            chart_sentiment=chart_sentiment,
            chart_response=chart_response,
            chart_intent=chart_intent,
            chart_satisfaction=chart_satisfaction,
            start_date=start_date,
            end_date=end_date,
        )
        
        return html
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        return f"""
        <html>
            <body style="background: #0f1419; color: #e5e7eb; font-family: sans-serif; padding: 40px;">
                <h1>Error Loading Dashboard</h1>
                <p>{str(e)}</p>
                <p>Please check your Supabase configuration and try again.</p>
            </body>
        </html>
        """

@app.get("/api/metrics")
async def get_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    API endpoint to get metrics as JSON
    
    Query Parameters:
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    """
    try:
        conversations = fetch_conversations_data(start_date, end_date)
        metrics = calculate_metrics(conversations)
        return {
            "status": "success",
            "data": metrics,
            "total_records": len(conversations)
        }
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        supabase = get_supabase_client()
        # Try to fetch one record to verify connection
        supabase.table("conversations").select("id").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║       College-Bot Analytics Dashboard                          ║
    ║       FastAPI + Plotly + Supabase                             ║
    ║                                                                ║
    ║       Starting server on http://0.0.0.0:{PORT}                ║
    ║       Dashboard: http://localhost:{PORT}                      ║
    ║       Health Check: http://localhost:{PORT}/api/health        ║
    ║       Metrics API: http://localhost:{PORT}/api/metrics        ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info" if DEBUG else "warning"
    )
