"""Shared Ollama client for HeritageAI."""

import json
import logging
import urllib.error
import urllib.request

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


class OllamaTimeoutError(RuntimeError):
    """Raised when Ollama does not finish a request before the timeout."""


def generate_response(
    prompt: str,
    *,
    num_predict: int | None = None,
) -> str:
    """Generate text through Ollama using the centralized application settings."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    settings = get_settings()

    options = {"temperature": 0.2}
    if num_predict is not None:
        if num_predict < 1:
            raise ValueError("num_predict must be at least 1.")
        options["num_predict"] = num_predict

    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
        "options": options,
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
            response_parts = []
            for line in response:
                if not line.strip():
                    continue

                result = json.loads(line.decode("utf-8"))
                if not isinstance(result, dict):
                    raise RuntimeError("Ollama returned an invalid response.")
                if "error" in result:
                    raise RuntimeError(
                        f"Ollama returned an error: {result['error']}"
                    )

                answer_part = result.get("response", "")
                if not isinstance(answer_part, str):
                    raise RuntimeError("Ollama returned an invalid response.")
                response_parts.append(answer_part)
                if result.get("done") is True:
                    break

    except TimeoutError as error:
        logger.warning("The Ollama request timed out.")
        raise OllamaTimeoutError(
            "The Ollama request timed out. Please try again later."
        ) from error
    except urllib.error.URLError as error:
        logger.warning("Could not connect to the Ollama service.")
        raise RuntimeError(
            "Could not connect to Ollama. Check that Ollama is running "
            "and the configured model is available."
        ) from error
    except OSError as error:
        logger.warning("The Ollama service request failed.")
        raise RuntimeError(
            "Could not connect to Ollama. Check that Ollama is running "
            "and the configured model is available."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Ollama returned an invalid response.") from error

    answer = "".join(response_parts)
    if not answer.strip():
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