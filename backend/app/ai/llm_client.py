
import json
import urllib.error
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


def generate_response(prompt: str) -> str:
    """
    Send a prompt to Ollama and return the generated text.
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.URLError as error:
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running "
            "and the llama3.2 model is available."
        ) from error

    answer = result.get("response", "").strip()

    if not answer:
        raise RuntimeError("Ollama returned an empty response.")

    return answer


if __name__ == "__main__":
    test_prompt = (
        "You are a helpful assistant. "
        "Reply with exactly: Ollama connection successful."
    )

    print(generate_response(test_prompt))
