import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = None
if supabase_url and supabase_key:
  supabase = create_client(supabase_url, supabase_key)


class ChatRequest(BaseModel):
  message: str


@app.get("/")
def home():
  return {"status": "Vento AI Backend Active"}


@app.post("/chat")
def chat(request: ChatRequest):
  api_key = os.environ.get("GEMINI_API_KEY")

  if not api_key:
    return {
        "reply": "خطأ: لم يتم إيجاد مفتاح GEMINI_API_KEY في إعدادات Render."
    }

  reply_text = ""

  try:
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=request.message,
    )
    reply_text = interaction.output_text
  except Exception as e:
    reply_text = f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {str(e)}"

  # Save to Supabase (only if it was configured correctly)
  if supabase:
    try:
      supabase.table("messages").insert({
          "message": request.message,
          "reply": reply_text,
      }).execute()
    except Exception as db_error:
      # Don't break the chat reply if saving fails, just log it
      print(f"Supabase save error: {db_error}")

  return {"reply": reply_text}
