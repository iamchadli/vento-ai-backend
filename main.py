import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
  genai.configure(api_key=api_key)


class ChatRequest(BaseModel):
  message: str


@app.get("/")
def home():
  return {"status": "Vento AI Backend is Live!"}


@app.post("/chat")
def chat(request: ChatRequest):
  if not api_key:
    return {
        "reply": "خطأ: لم يتم إيجاد مفتاح GEMINI_API_KEY في Environment Variables على Render."
    }

  try:
    # تجربة النموذج الافتراضي
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(request.message)
    return {"reply": response.text}
  except Exception as e:
    # إرجاع تفاصيل الخطأ مباشرة للواجهة لمعرفتها
    return {"reply": f"حدث خطأ في الذكاء الاصطناعي: {str(e)}"}
