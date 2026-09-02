import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# السماح للواجهة بالاتصال بالباك إند (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# إعداد نموذج الذكاء الاصطناعي
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
  genai.configure(api_key=api_key)


class ChatRequest(BaseModel):
  message: str


@app.get("/")
def home():
  return {"status": "Vento AI Backend is running successfully!"}


@app.post("/chat")
def chat(request: ChatRequest):
  if not api_key:
    raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing")

  try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(request.message)
    return {"reply": response.text}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
