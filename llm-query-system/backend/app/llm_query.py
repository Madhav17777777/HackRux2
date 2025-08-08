# ---------- llm_query.py ----------
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def gemini_query(prompt):
    response = model.generate_content(prompt)
    return response.text

