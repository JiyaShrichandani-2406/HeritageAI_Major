"""Shared Ollama client for HeritageAI."""

import json
import logging
import urllib.error
import urllib.request

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


def generate_response(prompt: str) -> str:
    """Generate text through Ollama using the centralized application settings."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    settings = get_settings()

    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    request = urllib.request.Request(
        settings.ollama_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=settings.ollama_timeout_seconds,
        ) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.URLError as error:
        logger.warning("Could not connect to the Ollama service.")
        raise RuntimeError(
            "Could not connect to Ollama. Check that Ollama is running "
            "and the configured model is available."
        ) from error

    if not isinstance(result, dict):
        raise RuntimeError("Ollama returned an invalid response.")

    answer = result.get("response", "")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Ollama returned an empty response.")

    return answer.strip()


if __name__ == "__main__":
    test_prompt = (
        "Return a JSON object with one key, status, "
        "whose value is Ollama connection successful."
    )

    try:
        print(generate_response(test_prompt))
    except (RuntimeError, ValueError) as error:
        print(f"LLM client error: {error}")