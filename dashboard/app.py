"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    COLLEGE-BOT INTELLIGENCE PLATFORM                         ║
║                    Enterprise-Grade Analytics Dashboard                      ║
║                                                                              ║
║  A Fortune 500-level strategic intelligence system designed to impress      ║
║  institutional leaders, deans, and investors with sophisticated analytics,  ║
║  predictive insights, and executive-level decision support.                 ║
║                                                                              ║
║  Technology: FastAPI + Plotly + Supabase                                    ║
║  Design Philosophy: Premium aesthetics, strategic storytelling, ROI focus   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from functools import lru_cache
import statistics

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from supabase import create_client, Client
import numpy as np

# ============================================================================
# CONFIGURATION & INITIALIZATION
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables required")

logging.basicConfig(level=logging.INFO if DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="College-Bot Intelligence Platform",
    description="Enterprise-grade analytics for institutional decision-making",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# ADVANCED DATA PROCESSING
# ============================================================================

def fetch_conversations_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """Fetch conversation data with advanced filtering"""
    try:
        supabase = get_supabase_client()
        query = supabase.table("conversations").select("*")
        
        if start_date:
            query = query.gte("created_at", f"{start_date}T00:00:00")
        if end_date:
            query = query.lte("created_at", f"{end_date}T23:59:59")
        
        response = query.order("created_at", desc=True).limit(5000).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return []

def calculate_advanced_metrics(conversations: List[Dict]) -> Dict[str, Any]:
    """Calculate Fortune 500-level metrics with predictive insights"""
    if not conversations:
        return get_empty_metrics()
    
    total = len(conversations)
    
    # Response time analysis
    response_times = [c.get("response_time", 0) for c in conversations if c.get("response_time")]
    avg_response = statistics.mean(response_times) if response_times else 0
    median_response = statistics.median(response_times) if response_times else 0
    p95_response = np.percentile(response_times, 95) if response_times else 0
    
    # Sentiment analysis
    sentiments = [c.get("sentiment", "neutral") for c in conversations]
    positive = sentiments.count("positive")
    negative = sentiments.count("negative")
    positive_rate = (positive / total * 100) if total > 0 else 0
    
    # Escalation analysis
    escalated = sum(1 for c in conversations if c.get("escalated", False))
    escalation_rate = (escalated / total * 100) if total > 0 else 0
    
    # Satisfaction analysis
    satisfaction_scores = [c.get("satisfaction_score", 0) for c in conversations if c.get("satisfaction_score")]
    avg_satisfaction = statistics.mean(satisfaction_scores) if satisfaction_scores else 0
    
    # Intent distribution
    intents = [c.get("intent", "unknown") for c in conversations]
    intent_diversity = len(set(intents))
    
    # Calculate ROI metrics
    monthly_conversations = total  # Assuming this is monthly data
    avg_labor_cost_per_query = 2.50  # $2.50 per manual query
    automated_queries = int(total * (1 - escalation_rate / 100))
    monthly_savings = automated_queries * avg_labor_cost_per_query
    annual_savings = monthly_savings * 12
    
    # Calculate efficiency score (0-100)
    efficiency_score = (
        (positive_rate / 100 * 40) +  # Sentiment: 40%
        ((100 - escalation_rate) / 100 * 30) +  # Resolution: 30%
        ((100 - (avg_response / 10)) / 100 * 20) +  # Speed: 20%
        ((avg_satisfaction / 100) * 10)  # Satisfaction: 10%
    )
    efficiency_score = min(100, max(0, efficiency_score))
    
    # Trend calculation (simplified - compare first half vs second half)
    mid_point = len(conversations) // 2
    first_half_sentiment = sum(1 for c in conversations[:mid_point] if c.get("sentiment") == "positive") / max(1, mid_point) * 100
    second_half_sentiment = sum(1 for c in conversations[mid_point:] if c.get("sentiment") == "positive") / max(1, len(conversations) - mid_point) * 100
    sentiment_trend = second_half_sentiment - first_half_sentiment
    
    return {
        "total_conversations": total,
        "avg_response_time": round(avg_response, 2),
        "median_response_time": round(median_response, 2),
        "p95_response_time": round(p95_response, 2),
        "positive_sentiment_rate": round(positive_rate, 1),
        "negative_sentiment_rate": round((negative / total * 100), 1),
        "escalation_rate": round(escalation_rate, 1),
        "avg_satisfaction": round(avg_satisfaction, 1),
        "intent_diversity": intent_diversity,
        "monthly_savings": round(monthly_savings, 2),
        "annual_savings": round(annual_savings, 2),
        "efficiency_score": round(efficiency_score, 1),
        "sentiment_trend": round(sentiment_trend, 1),
        "automated_queries": automated_queries,
        "escalated_queries": escalated,
    }

def get_empty_metrics() -> Dict[str, Any]:
    """Return empty metrics structure"""
    return {
        "total_conversations": 0,
        "avg_response_time": 0,
        "median_response_time": 0,
        "p95_response_time": 0,
        "positive_sentiment_rate": 0,
        "negative_sentiment_rate": 0,
        "escalation_rate": 0,
        "avg_satisfaction": 0,
        "intent_diversity": 0,
        "monthly_savings": 0,
        "annual_savings": 0,
        "efficiency_score": 0,
        "sentiment_trend": 0,
        "automated_queries": 0,
        "escalated_queries": 0,
    }

# ============================================================================
# PREMIUM CHART GENERATION
# ============================================================================

def generate_kpi_dashboard(metrics: Dict[str, Any]) -> str:
    """Generate executive KPI summary with premium styling"""
    
    kpis = [
        {
            "title": "Annual ROI Impact",
            "value": f"${metrics['annual_savings']:,.0f}",
            "subtitle": "Projected annual savings",
            "color": "#10b981",
            "icon": "💰"
        },
        {
            "title": "System Efficiency",
            "value": f"{metrics['efficiency_score']:.1f}%",
            "subtitle": "Overall performance score",
            "color": "#3b82f6",
            "icon": "⚡"
        },
        {
            "title": "Student Satisfaction",
            "value": f"{metrics['avg_satisfaction']:.1f}/10",
            "subtitle": "Average satisfaction rating",
            "color": "#8b5cf6",
            "icon": "😊"
        },
        {
            "title": "Resolution Rate",
            "value": f"{100 - metrics['escalation_rate']:.1f}%",
            "subtitle": "Queries resolved automatically",
            "color": "#f59e0b",
            "icon": "✅"
        },
    ]
    
    kpi_html = ""
    for kpi in kpis:
        kpi_html += f"""
        <div class="kpi-card" style="border-left: 4px solid {kpi['color']};">
            <div class="kpi-icon">{kpi['icon']}</div>
            <div class="kpi-content">
                <div class="kpi-title">{kpi['title']}</div>
                <div class="kpi-value" style="color: {kpi['color']};">{kpi['value']}</div>
                <div class="kpi-subtitle">{kpi['subtitle']}</div>
            </div>
        </div>
        """
    
    return kpi_html

def generate_premium_line_chart(conversations: List[Dict]) -> str:
    """Generate premium conversation volume trend with predictions"""
    if not conversations:
        return "<div class='no-data'>Insufficient data for visualization</div>"
    
    # Group by date
    date_counts = {}
    for conv in conversations:
        if conv.get("created_at"):
            date = conv["created_at"][:10]
            date_counts[date] = date_counts.get(date, 0) + 1
    
    dates = sorted(date_counts.keys())
    counts = [date_counts[date] for date in dates]
    
    # Calculate trend line
    x_numeric = np.arange(len(dates))
    z = np.polyfit(x_numeric, counts, 2)
    p = np.poly1d(z)
    trend_line = p(x_numeric)
    
    fig = go.Figure()
    
    # Actual data
    fig.add_trace(go.Scatter(
        x=dates, y=counts,
        mode='lines+markers',
        name='Actual Volume',
        line=dict(color='#3b82f6', width=4),
        marker=dict(size=10, symbol='circle', line=dict(width=2, color='white')),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.15)',
        hovertemplate='<b>%{x}</b><br>Conversations: %{y}<extra></extra>',
    ))
    
    # Trend line
    fig.add_trace(go.Scatter(
        x=dates, y=trend_line,
        mode='lines',
        name='Trend',
        line=dict(color='#8b5cf6', width=3, dash='dash'),
        hovertemplate='<b>%{x}</b><br>Trend: %{y:.0f}<extra></extra>',
    ))
    
    fig.update_layout(
        title={
            'text': '<b>Conversation Volume Trajectory</b><br><sub>Strategic growth analysis with trend projection</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#ffffff'}
        },
        xaxis_title='Date',
        yaxis_title='Volume',
        template='plotly_dark',
        plot_bgcolor='rgba(15, 20, 25, 0.3)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb', size=12),
        height=450,
        hovermode='x unified',
        showlegend=True,
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.3)', bordercolor='rgba(59,130,246,0.3)', borderwidth=1),
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_volume")

def generate_premium_sentiment_chart(conversations: List[Dict]) -> str:
    """Generate premium sentiment analysis with psychological insights"""
    if not conversations:
        return "<div class='no-data'>Insufficient data</div>"
    
    sentiments = [c.get("sentiment", "neutral") for c in conversations]
    sentiment_counts = {
        "positive": sentiments.count("positive"),
        "neutral": sentiments.count("neutral"),
        "negative": sentiments.count("negative"),
    }
    
    colors = ["#10b981", "#6b7280", "#ef4444"]
    labels = ["Positive", "Neutral", "Negative"]
    values = [sentiment_counts["positive"], sentiment_counts["neutral"], sentiment_counts["negative"]]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color='rgba(26,31,46,1)', width=3)),
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=14, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
    )])
    
    fig.update_layout(
        title={
            'text': '<b>Sentiment Distribution</b><br><sub>User satisfaction landscape analysis</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#ffffff'}
        },
        template='plotly_dark',
        plot_bgcolor='rgba(15, 20, 25, 0.3)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=450,
        showlegend=True,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_sentiment")

def generate_performance_radar(metrics: Dict[str, Any]) -> str:
    """Generate multi-dimensional performance radar chart"""
    
    categories = [
        'Response Speed',
        'Sentiment Score',
        'Resolution Rate',
        'Satisfaction',
        'System Efficiency'
    ]
    
    values = [
        min(100, (100 - (metrics['avg_response_time'] / 10))),  # Speed (0-100)
        metrics['positive_sentiment_rate'],  # Sentiment
        (100 - metrics['escalation_rate']),  # Resolution
        metrics['avg_satisfaction'] * 10,  # Satisfaction (0-100)
        metrics['efficiency_score'],  # Efficiency
    ]
    
    # Benchmark values (what excellence looks like)
    benchmark = [95, 90, 95, 95, 95]
    
    fig = go.Figure()
    
    # Actual performance
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current Performance',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=10, color='#3b82f6'),
        fillcolor='rgba(59, 130, 246, 0.25)',
    ))
    
    # Benchmark
    fig.add_trace(go.Scatterpolar(
        r=benchmark,
        theta=categories,
        fill='toself',
        name='Excellence Benchmark',
        line=dict(color='#8b5cf6', width=2, dash='dash'),
        marker=dict(size=8, color='#8b5cf6'),
        fillcolor='rgba(139, 92, 246, 0.1)',
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color='#9ca3af'),
                gridcolor='rgba(59, 130, 246, 0.2)',
            ),
            angularaxis=dict(
                tickfont=dict(color='#e5e7eb', size=12),
            ),
            bgcolor='rgba(15, 20, 25, 0.3)',
        ),
        title={
            'text': '<b>Performance Dimensions</b><br><sub>Multi-factor excellence analysis</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#ffffff'}
        },
        template='plotly_dark',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=450,
        showlegend=True,
        legend=dict(x=0.85, y=0.95),
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_radar")

def generate_response_time_distribution(conversations: List[Dict]) -> str:
    """Generate response time analysis with SLA visualization"""
    if not conversations:
        return "<div class='no-data'>Insufficient data</div>"
    
    response_times = [c.get("response_time", 0) for c in conversations if c.get("response_time")]
    
    if not response_times:
        return "<div class='no-data'>No response time data</div>"
    
    # Create histogram
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=response_times,
        nbinsx=30,
        marker=dict(color='#06b6d4', line=dict(color='white', width=1)),
        name='Response Time Distribution',
        hovertemplate='<b>Response Time Range</b><br>%{x}s<br>Frequency: %{y}<extra></extra>',
    ))
    
    # Add SLA line (e.g., 5 seconds)
    sla_target = 5
    fig.add_vline(
        x=sla_target,
        line_dash="dash",
        line_color="#f59e0b",
        annotation_text="SLA Target (5s)",
        annotation_position="top right",
    )
    
    fig.update_layout(
        title={
            'text': '<b>Response Time Analysis</b><br><sub>SLA compliance and performance distribution</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#ffffff'}
        },
        xaxis_title='Response Time (seconds)',
        yaxis_title='Frequency',
        template='plotly_dark',
        plot_bgcolor='rgba(15, 20, 25, 0.3)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=450,
        showlegend=False,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_response")

def generate_intent_analysis(conversations: List[Dict]) -> str:
    """Generate intent distribution with business insights"""
    if not conversations:
        return "<div class='no-data'>Insufficient data</div>"
    
    intents = [c.get("intent", "unknown") for c in conversations]
    intent_counts = {}
    for intent in intents:
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    # Top 12 intents
    top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:12]
    labels = [item[0] for item in top_intents]
    values = [item[1] for item in top_intents]
    
    fig = go.Figure(data=[go.Bar(
        y=labels,
        x=values,
        orientation='h',
        marker=dict(
            color=values,
            colorscale='Viridis',
            line=dict(color='white', width=1),
        ),
        text=values,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Queries: %{x}<extra></extra>',
    )])
    
    fig.update_layout(
        title={
            'text': '<b>Query Intent Landscape</b><br><sub>Top 12 student inquiry categories</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#ffffff'}
        },
        xaxis_title='Query Count',
        yaxis_title='Intent Category',
        template='plotly_dark',
        plot_bgcolor='rgba(15, 20, 25, 0.3)',
        paper_bgcolor='rgba(26, 31, 46, 0)',
        font=dict(color='#e5e7eb'),
        height=450,
        showlegend=False,
    )
    
    return fig.to_html(include_plotlyjs=False, div_id="chart_intent")

# ============================================================================
# PREMIUM HTML TEMPLATE
# ============================================================================

def generate_premium_html(
    metrics: Dict[str, Any],
    kpi_dashboard: str,
    chart_volume: str,
    chart_sentiment: str,
    chart_radar: str,
    chart_response: str,
    chart_intent: str,
    start_date: str,
    end_date: str,
) -> str:
    """Generate Fortune 500-level HTML dashboard"""
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>College-Bot Intelligence Platform</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
                color: #e5e7eb;
                font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
                min-height: 100vh;
                padding: 0;
                overflow-x: hidden;
            }}
            
            .container {{
                max-width: 1600px;
                margin: 0 auto;
                padding: 40px 20px;
            }}
            
            /* HEADER SECTION */
            header {{
                background: linear-gradient(135deg, rgba(26, 31, 46, 0.95) 0%, rgba(15, 20, 25, 0.95) 100%);
                border-bottom: 2px solid rgba(59, 130, 246, 0.3);
                padding: 40px;
                margin-bottom: 40px;
                border-radius: 16px;
                backdrop-filter: blur(10px);
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            }}
            
            .header-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            
            .header-title {{
                flex: 1;
            }}
            
            h1 {{
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 3em;
                font-weight: 900;
                letter-spacing: -1px;
                margin-bottom: 10px;
            }}
            
            .subtitle {{
                color: #9ca3af;
                font-size: 1.1em;
                font-weight: 300;
                letter-spacing: 0.5px;
            }}
            
            .header-badge {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 12px 24px;
                border-radius: 50px;
                font-size: 0.9em;
                font-weight: 600;
                display: inline-block;
                box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2);
            }}
            
            /* FILTER SECTION */
            .filter-section {{
                background: rgba(26, 31, 46, 0.7);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 40px;
                display: flex;
                gap: 20px;
                align-items: flex-end;
                flex-wrap: wrap;
                backdrop-filter: blur(10px);
            }}
            
            .filter-group {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            
            .filter-group label {{
                font-size: 0.85em;
                color: #9ca3af;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .filter-group input {{
                padding: 12px 16px;
                background: rgba(15, 20, 25, 0.8);
                border: 2px solid rgba(59, 130, 246, 0.3);
                border-radius: 8px;
                color: #e5e7eb;
                font-size: 0.95em;
                transition: all 0.3s ease;
                font-weight: 500;
            }}
            
            .filter-group input:focus {{
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
                background: rgba(15, 20, 25, 0.95);
            }}
            
            button {{
                padding: 12px 32px;
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.95em;
                letter-spacing: 0.5px;
                box-shadow: 0 10px 20px rgba(59, 130, 246, 0.2);
            }}
            
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 15px 30px rgba(59, 130, 246, 0.3);
            }}
            
            button:active {{
                transform: translateY(0);
            }}
            
            button.secondary {{
                background: rgba(59, 130, 246, 0.2);
                color: #3b82f6;
                border: 1px solid rgba(59, 130, 246, 0.4);
            }}
            
            /* KPI SECTION */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 24px;
                margin-bottom: 40px;
            }}
            
            .kpi-card {{
                background: linear-gradient(135deg, rgba(26, 31, 46, 0.9) 0%, rgba(15, 20, 25, 0.9) 100%);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 28px;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                position: relative;
                overflow: hidden;
            }}
            
            .kpi-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, currentColor, transparent);
                opacity: 0.5;
            }}
            
            .kpi-card:hover {{
                border-color: rgba(59, 130, 246, 0.5);
                transform: translateY(-8px);
                box-shadow: 0 20px 40px rgba(59, 130, 246, 0.15);
            }}
            
            .kpi-icon {{
                font-size: 2.5em;
                margin-bottom: 12px;
            }}
            
            .kpi-title {{
                color: #9ca3af;
                font-size: 0.85em;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }}
            
            .kpi-value {{
                font-size: 2.2em;
                font-weight: 900;
                margin-bottom: 8px;
                letter-spacing: -0.5px;
            }}
            
            .kpi-subtitle {{
                color: #6b7280;
                font-size: 0.85em;
                font-weight: 400;
            }}
            
            /* CHARTS SECTION */
            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(550px, 1fr));
                gap: 24px;
                margin-bottom: 40px;
            }}
            
            .chart-card {{
                background: linear-gradient(135deg, rgba(26, 31, 46, 0.9) 0%, rgba(15, 20, 25, 0.9) 100%);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 12px;
                padding: 24px;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            }}
            
            .chart-card:hover {{
                border-color: rgba(59, 130, 246, 0.4);
                box-shadow: 0 20px 50px rgba(59, 130, 246, 0.1);
            }}
            
            .chart-card h3 {{
                color: #e5e7eb;
                margin-bottom: 16px;
                font-size: 1.3em;
                font-weight: 700;
            }}
            
            /* FOOTER */
            footer {{
                text-align: center;
                color: #6b7280;
                font-size: 0.9em;
                margin-top: 60px;
                padding-top: 30px;
                border-top: 1px solid rgba(59, 130, 246, 0.1);
            }}
            
            .footer-text {{
                margin-bottom: 10px;
            }}
            
            .footer-badge {{
                display: inline-block;
                background: rgba(59, 130, 246, 0.1);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.8em;
                color: #3b82f6;
                margin-top: 10px;
            }}
            
            /* RESPONSIVE */
            @media (max-width: 1024px) {{
                .charts-grid {{
                    grid-template-columns: 1fr;
                }}
                
                h1 {{
                    font-size: 2.2em;
                }}
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px 15px;
                }}
                
                header {{
                    padding: 24px;
                }}
                
                h1 {{
                    font-size: 1.8em;
                }}
                
                .header-top {{
                    flex-direction: column;
                    gap: 16px;
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
                
                .kpi-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            
            /* ANIMATIONS */
            @keyframes fadeIn {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .kpi-card, .chart-card {{
                animation: fadeIn 0.6s ease-out forwards;
            }}
            
            .kpi-card:nth-child(1) {{ animation-delay: 0.1s; }}
            .kpi-card:nth-child(2) {{ animation-delay: 0.2s; }}
            .kpi-card:nth-child(3) {{ animation-delay: 0.3s; }}
            .kpi-card:nth-child(4) {{ animation-delay: 0.4s; }}
            .chart-card:nth-child(1) {{ animation-delay: 0.5s; }}
            .chart-card:nth-child(2) {{ animation-delay: 0.6s; }}
            .chart-card:nth-child(3) {{ animation-delay: 0.7s; }}
            .chart-card:nth-child(4) {{ animation-delay: 0.8s; }}
            .chart-card:nth-child(5) {{ animation-delay: 0.9s; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- HEADER -->
            <header>
                <div class="header-top">
                    <div class="header-title">
                        <h1>College-Bot Intelligence</h1>
                        <p class="subtitle">Enterprise Strategic Analytics Platform</p>
                    </div>
                    <div class="header-badge">🚀 LIVE DASHBOARD</div>
                </div>
            </header>
            
            <!-- FILTERS -->
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
                <button onclick="resetFilters()" class="secondary">Reset</button>
            </div>
            
            <!-- KPI DASHBOARD -->
            <div class="kpi-grid">
                {kpi_dashboard}
            </div>
            
            <!-- CHARTS -->
            <div class="charts-grid">
                <div class="chart-card">{chart_volume}</div>
                <div class="chart-card">{chart_sentiment}</div>
                <div class="chart-card">{chart_radar}</div>
                <div class="chart-card">{chart_response}</div>
                <div class="chart-card">{chart_intent}</div>
            </div>
            
            <!-- FOOTER -->
            <footer>
                <div class="footer-text">
                    College-Bot Intelligence Platform • Enterprise Analytics Engine
                </div>
                <div class="footer-text" style="font-size: 0.8em; color: #4b5563;">
                    Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
                </div>
                <div class="footer-badge">
                    ✓ Powered by FastAPI + Plotly + Supabase
                </div>
            </footer>
        </div>
        
        <script>
            function applyFilters() {{
                const startDate = document.getElementById('start_date').value;
                const endDate = document.getElementById('end_date').value;
                
                if (!startDate || !endDate) {{
                    alert('Please select both dates');
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
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Main dashboard - Fortune 500 level"""
    try:
        # Default date range
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Fetch and process data
        conversations = fetch_conversations_data(start_date, end_date)
        metrics = calculate_advanced_metrics(conversations)
        
        # Generate components
        kpi_dashboard = generate_kpi_dashboard(metrics)
        chart_volume = generate_premium_line_chart(conversations)
        chart_sentiment = generate_premium_sentiment_chart(conversations)
        chart_radar = generate_performance_radar(metrics)
        chart_response = generate_response_time_distribution(conversations)
        chart_intent = generate_intent_analysis(conversations)
        
        # Generate HTML
        html = generate_premium_html(
            metrics=metrics,
            kpi_dashboard=kpi_dashboard,
            chart_volume=chart_volume,
            chart_sentiment=chart_sentiment,
            chart_radar=chart_radar,
            chart_response=chart_response,
            chart_intent=chart_intent,
            start_date=start_date,
            end_date=end_date,
        )
        
        return html
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return f"""
        <html>
            <body style="background: #0f1419; color: #e5e7eb; font-family: sans-serif; padding: 40px;">
                <h1>⚠️ Dashboard Error</h1>
                <p>Error: {str(e)}</p>
                <p>Please verify your Supabase configuration.</p>
            </body>
        </html>
        """

@app.get("/api/metrics")
async def get_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """API endpoint for metrics"""
    try:
        conversations = fetch_conversations_data(start_date, end_date)
        metrics = calculate_advanced_metrics(conversations)
        return {
            "status": "success",
            "data": metrics,
            "total_records": len(conversations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        supabase = get_supabase_client()
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
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║            🚀 COLLEGE-BOT INTELLIGENCE PLATFORM 2.0                      ║
    ║                                                                           ║
    ║        Enterprise-Grade Analytics Dashboard                              ║
    ║        Designed to Impress Institutional Leaders & Investors             ║
    ║                                                                           ║
    ║        🌐 Dashboard: http://0.0.0.0:{PORT}                              ║
    ║        📊 Metrics API: http://0.0.0.0:{PORT}/api/metrics                ║
    ║        ✓ Health Check: http://0.0.0.0:{PORT}/api/health                ║
    ║                                                                           ║
    ║        Technology: FastAPI + Plotly + Supabase                           ║
    ║        Design: Fortune 500 Enterprise Standards                          ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info" if DEBUG else "warning"
    )
