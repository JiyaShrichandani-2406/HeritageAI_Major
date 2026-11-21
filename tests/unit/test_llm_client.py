
import json
from unittest.mock import MagicMock

import pytest

from backend.app.ai import llm_client


def make_settings():
    return type(
        "Settings",
        (),
        {
            "cloudflare_account_id": "test-account",
            "cloudflare_api_token": "test-token",
            "cloudflare_text_model": "@cf/test/model",
            "cloudflare_timeout_seconds": 15,
        },
    )()


def mock_response(mock_urlopen, payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = response


def test_generate_response_uses_configured_settings(monkeypatch):
    settings = make_settings()
    monkeypatch.setattr(llm_client, "get_settings", lambda: settings)

    mock_urlopen = MagicMock()
    mock_response(
        mock_urlopen,
        {
            "success": True,
            "result": {"response": "  HeritageAI is ready.  "},
        },
    )
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        mock_urlopen,
    )

    result = llm_client.generate_response("Say hello")

    assert result == "HeritageAI is ready."

    args, kwargs = mock_urlopen.call_args
    request = args[0]

    assert request.full_url == (
        "https://api.cloudflare.com/client/v4/accounts/"
        "test-account/ai/run/@cf/test/model"
    )
    assert request.get_header("Authorization") == "Bearer test-token"
    assert kwargs["timeout"] == 15

    payload = json.loads(request.data.decode("utf-8"))
    assert payload["messages"] == [
        {"role": "user", "content": "Say hello"}
    ]
    assert payload["temperature"] == 0.2


def test_generate_response_rejects_empty_prompt(monkeypatch):
    mock_urlopen = MagicMock()
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        mock_urlopen,
    )

    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        llm_client.generate_response("   ")

    mock_urlopen.assert_not_called()


def test_generate_response_sets_output_limit(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )

    mock_urlopen = MagicMock()
    mock_response(
        mock_urlopen,
        {"success": True, "result": {"response": "Done"}},
    )
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        mock_urlopen,
    )

    assert (
        llm_client.generate_response("Say hello", num_predict=768)
        == "Done"
    )

    payload = json.loads(mock_urlopen.call_args.args[0].data.decode())
    assert payload["max_tokens"] == 768


def test_generate_response_preserves_json_mode_and_context_arguments(
    monkeypatch,
):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )

    mock_urlopen = MagicMock()
    mock_response(
        mock_urlopen,
        {"success": True, "result": {"response": "{}"}},
    )
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        mock_urlopen,
    )

    result = llm_client.generate_response(
        "Return JSON",
        json_mode=True,
        num_ctx=8192,
    )

    assert result == "{}"

    payload = json.loads(mock_urlopen.call_args.args[0].data.decode())
    assert "num_ctx" not in payload
    assert "format" not in payload


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"num_predict": 0}, "num_predict must be at least 1"),
        ({"num_ctx": 0}, "num_ctx must be at least 1"),
    ],
)
def test_generate_response_rejects_invalid_limits(kwargs, message):
    with pytest.raises(ValueError, match=message):
        llm_client.generate_response("Say hello", **kwargs)


@pytest.mark.parametrize(
    "setting, message",
    [
        ("cloudflare_account_id", "Cloudflare account ID"),
        ("cloudflare_api_token", "Cloudflare API token"),
    ],
)
def test_generate_response_rejects_missing_credentials(
    monkeypatch,
    setting,
    message,
):
    settings = make_settings()
    setattr(settings, setting, "")

    monkeypatch.setattr(llm_client, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match=message):
        llm_client.generate_response("Say hello")


def test_generate_response_handles_api_error(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )

    mock_urlopen = MagicMock()
    mock_response(
        mock_urlopen,
        {
            "success": False,
            "errors": [{"message": "Invalid model"}],
        },
    )
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        mock_urlopen,
    )

    with pytest.raises(RuntimeError, match="Invalid model"):
        llm_client.generate_response("Say hello")


def test_generate_response_handles_connection_failure(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        MagicMock(
            side_effect=llm_client.urllib.error.URLError("offline")
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Could not connect to Cloudflare",
    ):
        llm_client.generate_response("Say hello")


def test_generate_response_handles_timeout(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        MagicMock(side_effect=TimeoutError("request timed out")),
    )

    with pytest.raises(
        llm_client.CloudflareTimeoutError,
        match="Cloudflare Workers AI request timed out",
    ):
        llm_client.generate_response("Say hello")


def test_generate_response_handles_connection_reset(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        MagicMock(side_effect=ConnectionResetError("connection reset")),
    )

    with pytest.raises(
        RuntimeError,
        match="Could not connect to Cloudflare",
    ):
        llm_client.generate_response("Say hello")


@pytest.mark.parametrize(
    "response_payload",
    [
        {"success": True, "result": {"response": "   "}},
        {"success": True, "result": {}},
        {"success": True},
        [],
    ],
)
def test_generate_response_rejects_invalid_or_empty_output(
    monkeypatch,
    response_payload,
):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )

    mock_urlopen = MagicMock()
    mock_response(mock_urlopen, response_payload)
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        mock_urlopen,
    )

    with pytest.raises(RuntimeError):
        llm_client.generate_response("Say hello")


def test_generate_response_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "get_settings",
        make_settings,
    )

    response = MagicMock()
    response.read.return_value = b"not valid JSON"

    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = response
    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        mock_urlopen,
    )

    with pytest.raises(
        RuntimeError,
        match="Cloudflare returned an invalid JSON response",
    ):
        llm_client.generate_response("Say hello")
