from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from google import genai
from .prompts import mode_prompts
from .security import RewriteRequest, validate_input
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
PORT = int(os.environ.get("PORT", "8787"))
app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors to help debug 422 responses."""
    body = await request.body()
    logger.error(f"Validation error for request: {body.decode()[:200]}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422, content={"detail": exc.errors(), "body": body.decode()[:200]}
    )


@app.post("/rewrite")
def rewrite(req: RewriteRequest):
    # Log incoming request
    logger.info(
        f"Rewrite request - mode: {req.mode}, text length: {len(req.text)} chars"
    )
    logger.debug(f"Text preview: {req.text[:100]}...")

    # Validate input for security threats
    try:
        validated_text = validate_input(req.text)
        logger.info("Security validation passed")
    except Exception as e:
        logger.warning(f"Security validation failed: {str(e)}")
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
