# dashboard/app.py
import os
import gradio as gr
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def fetch_metrics():
    try:
        data = supabase.table("conversations").select("*", count="exact").execute()
        return data.count or 0
    except:
        return 0

def fetch_logs():
    try:
        data = supabase.table("conversations") \
            .select("message_text, bot_response, timestamp") \
            .order("timestamp", desc=True) \
            .limit(10) \
            .execute()
        logs = []
        for row in data.data:
            time_str = row["timestamp"].split("T")[0]
            logs.append(f"[{time_str}] User: {row['message_text']}\n→ Bot: {row['bot_response']}\n")
        return "\n".join(reversed(logs)) if logs else "No data"
    except:
        return "Error loading logs"

with gr.Blocks() as demo:
    total_msg = gr.Number(label="Total Messages", value=0)
    logs = gr.Textbox(label="Recent Conversations", lines=12)
    refresh = gr.Button("🔄 Refresh")

    def update():
        return fetch_metrics(), fetch_logs()

    refresh.click(update, outputs=[total_msg, logs])
    demo.load(update, outputs=[total_msg, logs])

if __name__ == "__main__":
    # 🔥 THIS IS THE FIX 🔥
    port = int(os.environ.get("PORT", 7860))  # Must use os.environ, not os.getenv
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        auth=("admin", os.getenv("DASHBOARD_PASSWORD", "college123"))
    )