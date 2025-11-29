"""
🚀 Enterprise Command Center — Production-ready single-file FastAPI dashboard
Filename: dashboard_production_ready.py

This single-file app is a drop-in replacement for your dashboard. It keeps Plotly for visuals
but moves rendering to a fetch-driven frontend with a clean, minimalist, Fortune-500-ready
UI (responsive, accessible, hover effects, filters, export, auto-refresh).

How it's organized:
- FastAPI app with lifespan to initialize Supabase
- / (GET) serves a single HTML page (embedded template) with JS-driven controls
- /api/metrics (GET) returns JSON containing numeric KPIs and ready-made chart HTML
- /api/export (GET) returns CSV for the selected time-range and filters
- Lightweight in-memory TTL cache for metric queries to reduce supabase load

Drop this in your project, install dependencies, and run with uvicorn. See notes after the file.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import pandas as pd
import json
import io
import time

# Data/visualization libraries
import plotly.express as px
import plotly.graph_objects as go

# Supabase client - keep same as your existing import
from supabase import create_client, Client as SupabaseClient

# --- Config (import from your config or env) ---
try:
    from bot.config import SUPABASE_URL, SUPABASE_KEY, ENVIRONMENT, PORT
except Exception:
    # Fallbacks for local testing
    import os
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    PORT = int(os.environ.get('PORT', 8001))

# --- Logging ---
logging.basicConfig(level=logging.INFO if ENVIRONMENT != 'development' else logging.DEBUG)
logger = logging.getLogger("dashboard")

# --- App & lifecycle ---
supabase: Optional[SupabaseClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global supabase
    logger.info("Starting dashboard app and connecting to Supabase...")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Connected to Supabase.")
    except Exception as e:
        logger.exception("Failed to initialize Supabase client: %s", e)
        # App should still start for local dev, but metrics will return empty
        supabase = None
    yield
    logger.info("Shutting down dashboard app...")

app = FastAPI(title="Enterprise Command Center", version="2.1.0", lifespan=lifespan)

# Serve static folder if you choose to put assets there (optional)
# app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# --- Simple in-memory TTL cache to reduce Supabase calls ---
_METRIC_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 25  # short TTL to keep data fresh but reduce load


def _cache_key(start_iso: str, end_iso: str, intent: Optional[str], sentiment: Optional[str]):
    return f"{start_iso}|{end_iso}|{intent or 'ALL'}|{sentiment or 'ALL'}"


async def _fetch_conversation_metrics(start_date: datetime, end_date: datetime, intent: Optional[str] = None, sentiment: Optional[str] = None) -> Dict:
    """Fetch metrics from Supabase (sync queries wrapped in coroutine)."""
    # Check cache
    sk = _cache_key(start_date.isoformat(), end_date.isoformat(), intent, sentiment)
    cached = _METRIC_CACHE.get(sk)
    if cached and time.time() - cached['ts'] < CACHE_TTL_SECONDS:
        logger.debug("Returning cached metrics for %s", sk)
        return cached['value']

    # Default empty metrics
    result = {
        "total_interactions": 0,
        "avg_response_time": 0.0,
        "positive_sentiment_rate": 0.0,
        "escalated_conversations": 0,
        "intent_distribution": {},
        "sentiment_over_time": []
    }

    if not supabase:
        logger.warning("Supabase client not configured; returning empty metrics.")
        _METRIC_CACHE[sk] = {'ts': time.time(), 'value': result}
        return result

    # Build query (adjust column/table names to your schema)
    try:
        q = supabase.table('conversations').select('id, timestamp, sentiment, response_time_seconds, intent, urgency')
        q = q.gte('timestamp', start_date.isoformat()).lte('timestamp', end_date.isoformat())
        if intent:
            q = q.eq('intent', intent)
        if sentiment:
            q = q.eq('sentiment', sentiment)

        resp = q.execute()
        data = resp.data or []
        df = pd.DataFrame(data)

        if df.empty:
            _METRIC_CACHE[sk] = {'ts': time.time(), 'value': result}
            return result

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date

        total_interactions = len(df)
        avg_response_time = float(df['response_time_seconds'].mean()) if 'response_time_seconds' in df.columns else 0.0
        positive_count = df[df['sentiment'] == 'positive'].shape[0]
        negative_count = df[df['sentiment'] == 'negative'].shape[0]
        very_negative_count = df[df['sentiment'] == 'very_negative'].shape[0] if 'very_negative' in df['sentiment'].unique() else 0
        total_sentiment_count = positive_count + negative_count + very_negative_count
        positive_sentiment_rate = (positive_count / total_sentiment_count * 100) if total_sentiment_count > 0 else 0.0
        escalated_conversations = df[df['urgency'] == 'critical'].shape[0] + df[df['sentiment'] == 'very_negative'].shape[0]

        intent_counts = df['intent'].value_counts().to_dict() if 'intent' in df.columns else {}

        daily_sentiment = df.groupby('date')['sentiment'].value_counts().unstack(fill_value=0).reset_index()
        daily_sentiment['date_str'] = daily_sentiment['date'].astype(str)
        sentiment_over_time = daily_sentiment.to_dict(orient='records')

        result = {
            "total_interactions": int(total_interactions),
            "avg_response_time": round(avg_response_time, 2),
            "positive_sentiment_rate": round(positive_sentiment_rate, 2),
            "escalated_conversations": int(escalated_conversations),
            "intent_distribution": intent_counts,
            "sentiment_over_time": sentiment_over_time
        }

        _METRIC_CACHE[sk] = {'ts': time.time(), 'value': result}
        return result

    except Exception as e:
        logger.exception("Error fetching metrics: %s", e)
        return result


async def _fetch_real_time_status() -> Dict[str, Any]:
    if not supabase:
        return {"last_interaction": "No Data", "system_status": "No Data", "active_sessions": 0, "recent_errors": 0}
    try:
        last_q = supabase.table('conversations').select('timestamp').order('timestamp', desc=True).limit(1).execute()
        last = last_q.data[0] if last_q.data else None
        if last:
            last_ts = last['timestamp']
            last_dt = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
            delta = (datetime.now(timezone.utc) - last_dt).total_seconds()
            status = 'Operational' if delta < 300 else 'Degraded'
            return {"last_interaction": last_ts, "system_status": status, "active_sessions": 0, "recent_errors": 0}
        return {"last_interaction": "Never", "system_status": "No Data", "active_sessions": 0, "recent_errors": 0}
    except Exception as e:
        logger.exception("Error fetching real-time status: %s", e)
        return {"last_interaction": "Error", "system_status": "Error", "active_sessions": 0, "recent_errors": -1}


# --- Visualization helpers (return HTML fragments) ---

def create_interaction_volume_chart_html(sentiment_over_time: List[Dict]) -> str:
    if not sentiment_over_time:
        # Minimal fallback
        fig = px.line(x=[], y=[], title="Interactions Over Time")
    else:
        df = pd.DataFrame(sentiment_over_time)
        melt_cols = [c for c in df.columns if c not in ('date', 'date_str')]
        if not melt_cols:
            fig = px.line(x=df['date_str'], y=[0]*len(df), title='Interactions Over Time')
        else:
            df_melted = df.melt(id_vars=['date_str'], value_vars=melt_cols, var_name='sentiment', value_name='count')
            fig = px.area(df_melted, x='date_str', y='count', color='sentiment', title='Interaction Volume by Sentiment')

    fig.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified')
    return fig.to_html(include_plotlyjs=False, full_html=False)


def create_intent_pie_html(intent_counts: Dict[str, int]) -> str:
    if not intent_counts:
        fig = go.Figure(data=[go.Pie(labels=['No Data'], values=[1])])
    else:
        fig = px.pie(values=list(intent_counts.values()), names=list(intent_counts.keys()), title='Intent Distribution')
    fig.update_layout(template='plotly_white')
    return fig.to_html(include_plotlyjs=False, full_html=False)


def create_sentiment_gauge_html(positive_rate: float) -> str:
    fig = go.Figure(go.Indicator(mode='gauge+number', value=positive_rate, title={'text': 'Positive Sentiment (%)'},
                                 gauge={'axis': {'range': [0, 100]},
                                        'steps': [{'range': [0, 50], 'color': '#FFCDD2'},
                                                  {'range': [50, 75], 'color': '#FFF9C4'},
                                                  {'range': [75, 100], 'color': '#C8E6C9'}],
                                        'threshold': {'line': {'color': 'red', 'width': 4}, 'value': 80}}))
    fig.update_layout(template='plotly_white')
    return fig.to_html(include_plotlyjs=False, full_html=False)


# --- Routes ---
@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    # Embedded HTML template (clean, minimalist, responsive)
    html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Enterprise Command Center</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    :root{
      --bg: #0f1724; /* deep midnight */
      --card: rgba(255,255,255,0.03);
      --muted: #9aa6b2;
      --accent-1: linear-gradient(135deg,#667eea 0%,#8b5cf6 100%);
      --accent-2: #5eead4;
      --glass: rgba(255,255,255,0.03);
      --radius: 12px;
    }
    html,body{height:100%;margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial}
    body{background:var(--bg);color:#e6eef8;padding:28px}
    .app{max-width:1280px;margin:0 auto}
    header{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
    .brand{display:flex;align-items:center;gap:14px}
    .logo{width:48px;height:48px;border-radius:10px;background:var(--accent-1);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;box-shadow:0 6px 20px rgba(99,102,241,0.12)}
    h1{font-size:1.2rem;margin:0}
    p.lead{color:var(--muted);margin:0;font-size:0.9rem}

    /* Controls */
    .controls{display:flex;gap:12px;align-items:center}
    .control, button{background:var(--card);border:1px solid rgba(255,255,255,0.04);padding:8px 12px;border-radius:10px;color:inherit}
    .control:focus{outline:2px solid rgba(102,126,234,0.18)}
    button.primary{background:var(--accent-1);color:#fff;border:none;box-shadow:0 6px 18px rgba(99,102,241,0.12)}

    /* Grid */
    .grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
    .metric-card{grid-column:span 3;background:var(--glass);padding:18px;border-radius:var(--radius);transition:transform .18s ease, box-shadow .18s ease;border:1px solid rgba(255,255,255,0.03)}
    .metric-card:hover{transform:translateY(-6px);box-shadow:0 12px 30px rgba(2,6,23,0.6)}
    .metric-label{color:var(--muted);font-size:0.85rem}
    .metric-value{font-size:1.6rem;font-weight:700;margin-top:6px}

    /* Charts area */
    .card{background:var(--card);padding:18px;border-radius:var(--radius);grid-column:span 8;border:1px solid rgba(255,255,255,0.03)}
    .right-col{grid-column:span 4;display:flex;flex-direction:column;gap:16px}

    footer{color:var(--muted);text-align:center;margin-top:20px;font-size:0.85rem}

    @media (max-width:900px){
      .metric-card{grid-column:span 6}
      .card{grid-column:span 12}
      .right-col{grid-column:span 12}
      header{flex-direction:column;align-items:flex-start;gap:12px}
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="brand">
        <div class="logo">EC</div>
        <div>
          <h1>Enterprise Command Center</h1>
          <p class="lead">Real-time analytics · Bot performance · Customer safety</p>
        </div>
      </div>

      <div class="controls">
        <input id="start" class="control" type="date" />
        <input id="end" class="control" type="date" />
        <select id="intent" class="control"><option value="">All intents</option></select>
        <select id="sentiment" class="control"><option value="">All sentiment</option><option value="positive">Positive</option><option value="negative">Negative</option><option value="very_negative">Very Negative</option></select>
        <button id="apply" class="primary">Apply</button>
        <button id="export">Export CSV</button>
      </div>
    </header>

    <main class="grid">
      <div class="metric-card"><div class="metric-label">Total Interactions (range)</div><div id="kpi-total" class="metric-value">—</div></div>
      <div class="metric-card"><div class="metric-label">Avg. Response Time (s)</div><div id="kpi-avg" class="metric-value">—</div></div>
      <div class="metric-card"><div class="metric-label">Positive Sentiment</div><div id="kpi-pos" class="metric-value">—</div></div>
      <div class="metric-card"><div class="metric-label">Escalated Cases</div><div id="kpi-esc" class="metric-value">—</div></div>

      <section class="card" id="volume-card"><h3 style="margin-top:0">Interaction Volume</h3><div id="volume-chart">Loading…</div></section>

      <aside class="right-col">
        <div class="card" id="intent-card"><h3 style="margin-top:0">Intent Distribution</h3><div id="intent-chart">Loading…</div></div>
        <div class="card" id="gauge-card"><h3 style="margin-top:0">Sentiment Gauge</h3><div id="gauge-chart">Loading…</div></div>
      </aside>

      <div style="grid-column:span 12">
        <div class="card" id="raw-table" style="padding-bottom:6px"><h3 style="margin-top:0">Recent Conversations (sample)</h3><div id="table">Loading…</div></div>
      </div>

    </main>
    <footer>Enterprise Command Center · Data refreshed every 30s · Minimal, production-ready UI</footer>
  </div>

<script>
  // Utility: format ISO date to yyyy-mm-dd
  function toDateInput(d){
    const dt = new Date(d);
    const yyyy = dt.getFullYear();
    const mm = String(dt.getMonth()+1).padStart(2,'0');
    const dd = String(dt.getDate()).padStart(2,'0');
    return `${yyyy}-${mm}-${dd}`;
  }

  // Default date range: last 7 days
  const endEl = document.getElementById('end');
  const startEl = document.getElementById('start');
  const today = new Date();
  endEl.value = toDateInput(today);
  startEl.value = toDateInput(new Date(today.getTime() - (7*24*60*60*1000)));

  const intentSelect = document.getElementById('intent');
  const sentimentSelect = document.getElementById('sentiment');

  async function loadData(){
    const start = startEl.value;
    const end = endEl.value;
    const intent = intentSelect.value;
    const sentiment = sentimentSelect.value;
    const q = new URLSearchParams({start, end, intent, sentiment});
    try{
      const res = await fetch('/api/metrics?'+q.toString());
      const payload = await res.json();

      // KPIs
      document.getElementById('kpi-total').innerText = payload.total_interactions;
      document.getElementById('kpi-avg').innerText = payload.avg_response_time + 's';
      document.getElementById('kpi-pos').innerText = payload.positive_sentiment_rate + '%';
      document.getElementById('kpi-esc').innerText = payload.escalated_conversations;

      // Populate intents dropdown if not yet populated
      if(intentSelect.options.length <= 1){
        const intents = Object.keys(payload.intent_distribution || {});
        intents.forEach(i => { const opt = document.createElement('option'); opt.value = i; opt.text = i; intentSelect.appendChild(opt); });
      }

      // Charts (returned as HTML fragments using Plotly) - we must include plotly.js on the page (done)
      document.getElementById('volume-chart').innerHTML = payload.volume_html || '<small>No data</small>';
      document.getElementById('intent-chart').innerHTML = payload.intent_html || '<small>No data</small>';
      document.getElementById('gauge-chart').innerHTML = payload.gauge_html || '<small>No data</small>';

      // Table sample
      if(payload.sample && payload.sample.length){
        const rows = payload.sample.map(r => `<tr><td>${r.timestamp}</td><td>${r.intent||''}</td><td>${r.sentiment||''}</td><td>${r.response_time_seconds||''}</td></tr>`).join('');
        document.getElementById('table').innerHTML = `<table style="width:100%;border-collapse:collapse;color:inherit"><thead><tr style="text-align:left;color:var(--muted)"><th>Timestamp</th><th>Intent</th><th>Sentiment</th><th>Response (s)</th></tr></thead><tbody>${rows}</tbody></table>`;
      } else {
        document.getElementById('table').innerHTML = '<div style="color:var(--muted)">No recent rows.</div>';
      }

    }catch(err){
      console.error(err);
    }
  }

  document.getElementById('apply').addEventListener('click', ()=> loadData());

  // Auto-refresh every 30s
  setInterval(loadData, 30000);

  // Export
  document.getElementById('export').addEventListener('click', ()=>{
    const start = startEl.value;
    const end = endEl.value;
    const intent = intentSelect.value;
    const sentiment = sentimentSelect.value;
    window.open('/api/export?'+new URLSearchParams({start,end,intent,sentiment}).toString(), '_blank');
  });

  // Initial load
  loadData();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html)


@app.get('/api/metrics')
async def api_metrics(start: str = Query(...), end: str = Query(...), intent: Optional[str] = Query(None), sentiment: Optional[str] = Query(None)):
    """Returns KPI numbers plus chart HTML fragments for the frontend to render.
    Query params:
      start: YYYY-MM-DD
      end: YYYY-MM-DD
      intent: optional intent filter
      sentiment: optional sentiment filter
    """
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end) + timedelta(days=1) - timedelta(seconds=1)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid date format. Use YYYY-MM-DD')

    metrics = await _fetch_conversation_metrics(start_dt.replace(tzinfo=timezone.utc), end_dt.replace(tzinfo=timezone.utc), intent, sentiment)
    status = await _fetch_real_time_status()

    # Build charts
    volume_html = create_interaction_volume_chart_html(metrics.get('sentiment_over_time', []))
    intent_html = create_intent_pie_html(metrics.get('intent_distribution', {}))
    gauge_html = create_sentiment_gauge_html(metrics.get('positive_sentiment_rate', 0))

    # Provide a small sample of raw rows for table preview
    sample = []
    if supabase:
        try:
            q = supabase.table('conversations').select('timestamp, intent, sentiment, response_time_seconds').gte('timestamp', start_dt.isoformat()).lte('timestamp', end_dt.isoformat()).order('timestamp', desc=True).limit(10).execute()
            sample = q.data or []
        except Exception:
            sample = []

    return JSONResponse(content={
        'total_interactions': metrics['total_interactions'],
        'avg_response_time': metrics['avg_response_time'],
        'positive_sentiment_rate': metrics['positive_sentiment_rate'],
        'escalated_conversations': metrics['escalated_conversations'],
        'intent_distribution': metrics['intent_distribution'],
        'sentiment_over_time': metrics['sentiment_over_time'],
        'volume_html': volume_html,
        'intent_html': intent_html,
        'gauge_html': gauge_html,
        'sample': sample,
        'system_status': status
    })


@app.get('/api/export')
async def api_export(start: str = Query(...), end: str = Query(...), intent: Optional[str] = Query(None), sentiment: Optional[str] = Query(None)):
    """Return CSV for the selected query - useful for execs who want raw data."""
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end) + timedelta(days=1) - timedelta(seconds=1)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid date format. Use YYYY-MM-DD')

    # Fetch rows
    rows = []
    if supabase:
        try:
            q = supabase.table('conversations').select('*').gte('timestamp', start_dt.isoformat()).lte('timestamp', end_dt.isoformat())
            if intent:
                q = q.eq('intent', intent)
            if sentiment:
                q = q.eq('sentiment', sentiment)
            resp = q.execute()
            rows = resp.data or []
        except Exception:
            rows = []

    df = pd.DataFrame(rows)
    stream = io.StringIO()
    if not df.empty:
        df.to_csv(stream, index=False)
    else:
        stream.write('No rows')
    stream.seek(0)
    return StreamingResponse(iter([stream.read().encode()]), media_type='text/csv', headers={'Content-Disposition':'attachment; filename="export.csv"'})


@app.get('/health')
async def health():
    return {'status':'ok', 'service':'dashboard', 'time':datetime.now(timezone.utc).isoformat()}


# Run with: uvicorn dashboard_production_ready:app --host 0.0.0.0 --port 8001

# -------------------- NOTES --------------------
# - This single-file app returns Plotly fragments and loads plotly.js from CDN for speed.
# - Replace table/column names to match your Supabase schema if different.
# - For production: run behind an ASGI server (uvicorn + gunicorn), add HTTPS, authentication (OAuth2/JWT), and monitoring (Sentry).
# - Consider adding feature flags for 'demo' or 'sensitive' columns. Keep PII out of exports.
# - I used a small TTL cache to reduce repeating Supabase queries. Tune CACHE_TTL_SECONDS to your traffic.
# - Optional improvements: websocket push for live updates, role-based views, PDF/PNG snapshot exports, and a React frontend.
