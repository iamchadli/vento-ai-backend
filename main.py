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


class SignupRequest(BaseModel):
  email: str
  password: str
  username: str
  role: str  # "customer" or "seller"
  store_name: str = ""


class LoginRequest(BaseModel):
  email: str
  password: str


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

  if supabase:
    try:
      supabase.table("messages").insert({
          "message": request.message,
          "reply": reply_text,
      }).execute()
    except Exception as db_error:
      print(f"Supabase save error: {db_error}")

  return {"reply": reply_text}


@app.post("/signup")
def signup(request: SignupRequest):
  if not supabase:
    return {"success": False, "message": "قاعدة البيانات غير مهيأة على السيرفر."}

  try:
    auth_response = supabase.auth.sign_up({
        "email": request.email,
        "password": request.password,
    })

    if not auth_response.user:
      return {"success": False, "message": "تعذر إنشاء الحساب. حاول مجددًا."}

    user_id = auth_response.user.id

    try:
      supabase.table("profiles").insert({
          "user_id": user_id,
          "username": request.username,
          "role": request.role,
          "store_name": request.store_name,
          "contact": request.email,
      }).execute()
    except Exception as profile_error:
      print(f"Profile insert error: {profile_error}")

    return {
        "success": True,
        "message": "تم إنشاء الحساب! تحقق من بريدك الإلكتروني ودوس على رابط التأكيد قبل تسجيل الدخول."
    }

  except Exception as e:
    error_msg = str(e)
    if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
      return {"success": False, "message": "هذا البريد الإلكتروني مسجل بالفعل."}
    return {"success": False, "message": f"خطأ: {error_msg}"}


@app.post("/login")
def login(request: LoginRequest):
  if not supabase:
    return {"success": False, "message": "قاعدة البيانات غير مهيأة على السيرفر."}

  try:
    auth_response = supabase.auth.sign_in_with_password({
        "email": request.email,
        "password": request.password,
    })

    if not auth_response.user:
      return {"success": False, "message": "البريد الإلكتروني أو كلمة السر غير صحيحة."}

    user_id = auth_response.user.id

    profile_data = {"username": "", "role": "customer", "store_name": ""}
    try:
      profile_res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
      if profile_res.data and len(profile_res.data) > 0:
        profile_data = profile_res.data[0]
    except Exception as profile_error:
      print(f"Profile fetch error: {profile_error}")

    return {
        "success": True,
        "user": {
            "email": request.email,
            "username": profile_data.get("username", ""),
            "role": profile_data.get("role", "customer"),
            "store_name": profile_data.get("store_name", ""),
        }
    }

  except Exception as e:
    error_msg = str(e)
    if "email not confirmed" in error_msg.lower() or "not confirmed" in error_msg.lower():
      return {"success": False, "message": "يجب تأكيد بريدك الإلكتروني أولاً عبر الرابط المرسل إليك."}
    if "invalid" in error_msg.lower():
      return {"success": False, "message": "البريد الإلكتروني أو كلمة السر غير صحيحة."}
    return {"success": False, "message": f"خطأ: {error_msg}"}
