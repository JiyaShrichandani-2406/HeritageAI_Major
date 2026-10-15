import pytest
from pydantic import ValidationError

from backend.app.schemas.common import (
    CostStatus,
    ErrorResponse,
    HealthResponse,
    ValidationErrorResponse,
)


def test_health_response_has_exactly_the_agreed_fields():
    assert set(HealthResponse.model_fields) == {"status", "service", "version"}


def test_health_response_serializes_expected_values():
    response = HealthResponse(
        status="ok", service="heritageai-api", version="1.0.0"
    )

    assert response.model_dump() == {
        "status": "ok",
        "service": "heritageai-api",
        "version": "1.0.0",
    }


def test_health_response_rejects_unknown_status():
    with pytest.raises(ValidationError):
        HealthResponse(status="broken", service="x", version="1.0.0")


def test_health_response_requires_all_fields():
    with pytest.raises(ValidationError):
        HealthResponse(status="ok")


def test_health_response_rejects_extra_fields():
    with pytest.raises(ValidationError):
        HealthResponse(status="ok", service="x", version="1.0.0", uptime=5)


def test_cost_status_values_match_the_project_plan():
    assert [status.value for status in CostStatus] == [
        "verified",
        "estimated",
        "unavailable",
    ]


def test_cost_status_rejects_unknown_value():
    with pytest.raises(ValueError):
        CostStatus("free")


def test_error_response_wraps_detail_message():
    assert ErrorResponse(detail="Not found").model_dump() == {
        "detail": "Not found"
    }


def test_validation_error_response_accepts_fastapi_error_shape():
    payload = {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "question"],
                "msg": "Field required",
                "input": {},
            }
        ]
    }

    parsed = ValidationErrorResponse(**payload)

    assert parsed.detail[0].loc == ["body", "question"]
    assert parsed.detail[0].msg == "Field required"