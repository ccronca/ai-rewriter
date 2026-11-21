"""Provider-aware LLM completion: EnMaaS by default, Gemini when GEMINI_API_KEY is set."""

import os

from google import genai
from openai import OpenAI

ENMAAS_MODEL = "rits/zai-org/glm-5-3"


def complete(prompt: str) -> str:
    if os.environ.get("GEMINI_API_KEY"):
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
        )
        return (response.text or "").strip()
    if os.environ.get("ENMAAS_KEY"):
        base_url = os.environ.get("ENMAAS_BASE_URL")
        if not base_url:
            raise RuntimeError(
                "EnMaaS selected (ENMAAS_KEY is set) but ENMAAS_BASE_URL is not configured"
            )
        # shortcut: client built per call, fine at clipboard-rewrite volume; cache if this serves concurrent traffic
        client = OpenAI(base_url=base_url, api_key=os.environ["ENMAAS_KEY"])
        response = client.chat.completions.create(
            model=ENMAAS_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return (response.choices[0].message.content or "").strip()
    raise RuntimeError(
        "No LLM provider configured: set ENMAAS_KEY (EnMaaS) or GEMINI_API_KEY (Gemini)"
    )
