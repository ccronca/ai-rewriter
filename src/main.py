import os

from fastapi import FastAPI, HTTPException

from .models import RewriteRequest
from .prompts import mode_prompts
from .providers import ProviderError, generate
from .security import validate_input

PORT = int(os.environ.get("PORT", "8787"))
ENABLE_SECURITY = os.environ.get("ENABLE_SECURITY", "true").lower() == "true"
app = FastAPI()


@app.post("/rewrite")
def rewrite(req: RewriteRequest):
    if ENABLE_SECURITY:
        try:
            validated_text = validate_input(req.text)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Security validation failed: {str(e)}"
            )
    else:
        validated_text = req.text

    prompt = f"""
{mode_prompts.get(req.mode, mode_prompts['default'])}

Message:
{validated_text}
"""
    try:
        result = generate(prompt)
    except ProviderError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    return {"result": result}


@app.get("/health")
def health():
    return {"status": "ok"}
