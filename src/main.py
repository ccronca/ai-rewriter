from fastapi import FastAPI, HTTPException
from google import genai
from .prompts import mode_prompts
from .security import RewriteRequest, validate_input
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
PORT = int(os.environ.get("PORT", "8787"))
app = FastAPI()


@app.post("/rewrite")
def rewrite(req: RewriteRequest):
    # Validate input for security threats
    try:
        validated_text = validate_input(req.text)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Security validation failed: {str(e)}"
        )

    # Build prompt with validated input
    prompt = f"""
{mode_prompts.get(req.mode, mode_prompts['default'])}

Message:
{validated_text}
"""
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt,
    )
    return {"result": response.text.strip()}


@app.get("/health")
def health():
    return {"status": "ok"}
