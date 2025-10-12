# dashboard/app.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from supabase import create_client
from dotenv import load_dotenv
import gradio as gr

load_dotenv()

# Supabase
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
        return "Error"

# Gradio interface
with gr.Blocks(title="College Bot Admin") as demo:
    gr.Markdown("# 🎓 College WhatsApp Bot Dashboard")
    total_msg = gr.Number(label="Total Messages", value=0)
    logs = gr.Textbox(label="Recent Conversations", lines=12)
    refresh = gr.Button("🔄 Refresh")

    def update():
        return fetch_metrics(), fetch_logs()

    refresh.click(update, outputs=[total_msg, logs])
    demo.load(update, outputs=[total_msg, logs])

# FastAPI app
app = FastAPI()

# Mount Gradio as a sub-app
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)