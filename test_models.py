import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for m in ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-flash-latest", "gemini-3.5-flash"]:
    try:
        r = client.models.generate_content(model=m, contents="Reply with the word OK")
        print("WORKS   ", m, "->", r.text.strip()[:20])
    except Exception as e:
        print("FAILED  ", m, "->", str(e)[:80])