from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from .prompts import mode_prompts
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
PORT = int(os.environ.get("PORT", "8787"))
app = FastAPI()


class RewriteRequest(BaseModel):
    text: str
    mode: str = "default"


@app.post("/rewrite")
def rewrite(req: RewriteRequest):
    prompt = f"""
{mode_prompts.get(req.mode, mode_prompts['default'])}

Message:
{req.text}
"""
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt,
    )
    return {"result": response.text.strip()}


@app.get("/health")
def health():
    return {"status": "ok"}
