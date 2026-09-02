import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

  try:
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=request.message,
    )
    return {"reply": interaction.output_text}
  except Exception as e:
    return {"reply": f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {str(e)}"}
