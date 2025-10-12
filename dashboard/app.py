# dashboard/app.py
import os
import gradio as gr
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def fetch_metrics():
    """Fetch total message count"""
    try:
        data = supabase.table("conversations").select("*", count="exact").execute()
        return data.count or 0
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return 0

def fetch_logs():
    """Fetch recent conversation logs"""
    try:
        data = supabase.table("conversations") \
            .select("message_text, bot_response, timestamp") \
            .order("timestamp", desc=True) \
            .limit(10) \
            .execute()
        logs = []
        for row in data.data:
            time_str = row["timestamp"].split("T")[0]
            logs.append(
                f"[{time_str}] User: {row['message_text']}\n"
                f"→ Bot: {row['bot_response']}\n"
            )
        return "\n".join(reversed(logs)) if logs else "No conversations yet."
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return "Failed to load logs"

# Build Gradio interface
with gr.Blocks(title="College Bot Admin") as demo:
    gr.Markdown("# 🎓 College WhatsApp Bot Dashboard")
    
    with gr.Row():
        total_msg = gr.Number(label="Total Messages", value=0)
        logs = gr.Textbox(label="Recent Conversations", lines=12)
    
    refresh_btn = gr.Button("🔄 Refresh Data")

    def update_dashboard():
        total = fetch_metrics()
        conversation_logs = fetch_logs()
        return total, conversation_logs

    refresh_btn.click(update_dashboard, outputs=[total_msg, logs])
    demo.load(update_dashboard, outputs=[total_msg, logs])

# Launch
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", 7860)),
        auth=("admin", os.getenv("DASHBOARD_PASSWORD", "college123"))
    )