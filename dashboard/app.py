# dashboard/app.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

app = FastAPI()

def get_metrics():
    try:
        data = supabase.table("conversations").select("*", count="exact").execute()
        return data.count or 0
    except:
        return 0

def get_logs():
    try:
        data = supabase.table("conversations") \
            .select("message_text, bot_response, timestamp") \
            .order("timestamp", desc=True) \
            .limit(10) \
            .execute()
        logs = []
        for row in data.data:
            time_str = row["timestamp"].split("T")[0]
            logs.append(f"[{time_str}] User: {row['message_text']}<br>→ Bot: {row['bot_response']}<br><br>")
        return "".join(reversed(logs)) if logs else "No conversations yet."
    except:
        return "Error loading logs"

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    total = get_metrics()
    logs_html = get_logs()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>College Bot Admin</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .metrics {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .metric {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .logs {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .refresh {{ text-align: center; margin-top: 20px; }}
            button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 College WhatsApp Bot Dashboard</h1>
            </div>
            <div class="metrics">
                <div class="metric">
                    <h3>Total Messages</h3>
                    <p style="font-size: 24px;">{total}</p>
                </div>
            </div>
            <div class="logs">
                <h3>Recent Conversations</h3>
                <div>{logs_html}</div>
            </div>
            <div class="refresh">
                <button onclick="location.reload()">🔄 Refresh Data</button>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)