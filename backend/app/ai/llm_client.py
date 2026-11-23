
"""Shared Cloudflare Workers AI client for HeritageAI."""

import json
import logging
import urllib.error
import urllib.request

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


class CloudflareTimeoutError(RuntimeError):
    """Raised when Cloudflare AI does not respond before the timeout."""


def generate_response(
    prompt: str,
    *,
    num_predict: int | None = None,
    json_mode: bool = False,
    num_ctx: int | None = None,
) -> str:
    """Generate text using Cloudflare Workers AI."""

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    if num_predict is not None and num_predict < 1:
        raise ValueError("num_predict must be at least 1.")

    if num_ctx is not None and num_ctx < 1:
        raise ValueError("num_ctx must be at least 1.")

    settings = get_settings()

    if not settings.cloudflare_account_id:
        raise RuntimeError("Cloudflare account ID is not configured.")

    if not settings.cloudflare_api_token:
        raise RuntimeError("Cloudflare API token is not configured.")

    model = settings.cloudflare_text_model

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{settings.cloudflare_account_id}/ai/run/{model}"
    )

    payload = {
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
    }

    if num_predict is not None:
        payload["max_tokens"] = num_predict

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.cloudflare_api_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=settings.cloudflare_timeout_seconds,
        ) as response:
            raw_response = response.read().decode("utf-8")

        result = json.loads(raw_response)

        if not isinstance(result, dict):
            print(
                f"!!! CF RAW (not-dict): {raw_response[:800]}",
                flush=True,
            )
            raise RuntimeError("Cloudflare returned an invalid response.")

        if result.get("success") is False:
            errors = result.get("errors", [])
            message = "Cloudflare Workers AI request failed."

            if errors and isinstance(errors, list):
                first_error = errors[0]
                if isinstance(first_error, dict):
                    message = first_error.get("message", message)

            print(
                f"!!! CF success=False model={model!r} "
                f"errors={errors!r}",
                flush=True,
            )
            raise RuntimeError(message)

        model_result = result.get("result")

        if not isinstance(model_result, dict):
            print(
                f"!!! CF result not-dict model={model!r} "
                f"result_type={type(model_result).__name__} "
                f"raw={raw_response[:800]}",
                flush=True,
            )
            raise RuntimeError("Cloudflare returned an invalid response.")

        # Workers AI returns either the classic shape {"response": "..."}
        # or the OpenAI-compatible shape {"choices": [{"message": {"content": "..."}}]}
        # depending on the model. Accept both.
        answer = model_result.get("response")

        if not isinstance(answer, str):
            choices = model_result.get("choices")
            if isinstance(choices, list) and choices:
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get("message")
                    if isinstance(message, dict):
                        content = message.get("content")
                        if isinstance(content, str):
                            answer = content

        if not isinstance(answer, str):
            print(
                f"!!! CF response not-str model={model!r} "
                f"response_type={type(answer).__name__} "
                f"result_keys={list(model_result.keys())} "
                f"raw={raw_response[:800]}",
                flush=True,
            )
            raise RuntimeError("Cloudflare returned an invalid response.")

    except urllib.error.HTTPError as error:
        try:
            body = error.read().decode("utf-8", errors="replace")
        except Exception:
            body = "<unreadable>"
        print(
            f"!!! CF HTTP {error.code} model={model!r} body={body[:800]}",
            flush=True,
        )
        raise RuntimeError(
            f"Cloudflare Workers AI request failed with HTTP {error.code}."
        ) from error

    except (TimeoutError, OSError) as error:
        print(
            f"!!! CF conn/timeout model={model!r} error={error!r}",
            flush=True,
        )

        if isinstance(error, TimeoutError):
            raise CloudflareTimeoutError(
                "Cloudflare Workers AI request timed out. "
                "Please try again later."
            ) from error

        raise RuntimeError(
            "Could not connect to Cloudflare Workers AI. "
            "Check your network connection."
        ) from error

    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise CloudflareTimeoutError(
                "Cloudflare Workers AI request timed out. "
                "Please try again later."
            ) from error

        logger.warning("Could not connect to Cloudflare Workers AI.")
        raise RuntimeError(
            "Could not connect to Cloudflare Workers AI."
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Cloudflare returned an invalid JSON response."
        ) from error

    if not answer.strip():
        raise RuntimeError("Cloudflare returned an empty response.")

    return answer.strip()


if __name__ == "__main__":
    test_prompt = "Reply with: HeritageAI Cloudflare connection successful."

    try:
        print(generate_response(test_prompt))
    except (RuntimeError, ValueError) as error:
        print(f"LLM client error: {error}")
