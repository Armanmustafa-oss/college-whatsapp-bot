# dashboard/app.py
import os
import gradio as gr
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_metrics():
    total = supabase.table("conversations").select("id", count="exact").execute().count or 0
    return {"Total Messages": total}

def get_logs():
    data = supabase.table("conversations") \
        .select("message_text, bot_response, timestamp") \
        .order("timestamp", desc=True) \
        .limit(10) \
        .execute()
    logs = []
    for row in data.data:
        logs.append(f"[{row['timestamp'][:10]}] User: {row['message_text']}\nBot: {row['bot_response']}\n")
    return "\n".join(reversed(logs)) if logs else "No data yet."

with gr.Blocks(title="College Bot Admin") as demo:
    gr.Markdown("# 🎓 College WhatsApp Bot Dashboard")
    
    total_msg = gr.Number(label="Total Messages")
    logs = gr.Textbox(label="Recent Conversations", lines=10)
    refresh = gr.Button("🔄 Refresh")

    def update():
        m = get_metrics()
        return m["Total Messages"], get_logs()

    refresh.click(update, outputs=[total_msg, logs])
    demo.load(update, outputs=[total_msg, logs])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", 7860)),
        auth=("admin", os.getenv("DASHBOARD_PASSWORD", "college123"))
    )