import json
from unittest.mock import MagicMock

import pytest

from backend.app.ai import llm_client


def test_generate_response_uses_configured_settings(monkeypatch):
    settings = type("Settings", (), {
        "ollama_url": "http://test-ollama:11434/api/generate",
        "ollama_model": "test-model",
        "ollama_timeout_seconds": 15,
    })()

    monkeypatch.setattr(llm_client, "get_settings", lambda: settings)

    response = MagicMock()
    response.read.return_value = json.dumps(
        {"response": "  HeritageAI is ready.  "}
    ).encode("utf-8")

    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = response
    monkeypatch.setattr(llm_client.urllib.request, "urlopen", mock_urlopen)

    result = llm_client.generate_response("Say hello")

    assert result == "HeritageAI is ready."
    args, kwargs = mock_urlopen.call_args
    request = args[0]

    assert request.full_url == settings.ollama_url
    assert kwargs["timeout"] == 15

    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "test-model"
    assert payload["prompt"] == "Say hello"
    assert payload["stream"] is False


def test_generate_response_rejects_empty_prompt(monkeypatch):
    mock_urlopen = MagicMock()
    monkeypatch.setattr(llm_client.urllib.request, "urlopen", mock_urlopen)

    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        llm_client.generate_response("   ")

    mock_urlopen.assert_not_called()


def test_generate_response_handles_connection_failure(monkeypatch):
    settings = type("Settings", (), {
        "ollama_url": "http://test-ollama:11434/api/generate",
        "ollama_model": "test-model",
        "ollama_timeout_seconds": 15,
    })()

    monkeypatch.setattr(llm_client, "get_settings", lambda: settings)
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        MagicMock(
            side_effect=llm_client.urllib.error.URLError("offline")
        ),
    )

    with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
        llm_client.generate_response("Say hello")


def test_generate_response_rejects_empty_model_output(monkeypatch):
    settings = type("Settings", (), {
        "ollama_url": "http://test-ollama:11434/api/generate",
        "ollama_model": "test-model",
        "ollama_timeout_seconds": 15,
    })()

    monkeypatch.setattr(llm_client, "get_settings", lambda: settings)

    response = MagicMock()
    response.read.return_value = b'{"response": "   "}'

    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = response
    monkeypatch.setattr(llm_client.urllib.request, "urlopen", mock_urlopen)

    with pytest.raises(RuntimeError, match="Ollama returned an empty response"):
        llm_client.generate_response("Say hello")