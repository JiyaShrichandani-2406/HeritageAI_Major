
import pytest

from backend.app.schemas.itinerary import ItineraryRequest
from backend.app.services.itinerary_service import build_itinerary_response


@pytest.fixture
def sample_request():
    return ItineraryRequest(
        destination="Bhopal",
        budget=3000,
        days=2,
        interests=["history", "architecture"],
        travelers=1,
        travel_style="budget",
        include_food=True,
        include_transport=True,
    )


@pytest.fixture
def sample_daily_plans():
    return [
        {
            "title": "Day 1 - Historical Sites",
            "activities": [
                {
                    "place_name": "Historical Site A",
                    "description": "Explore the site's history.",
                    "estimated_entry_cost": 100,
                    "estimated_transport_cost": 50,
                    "estimated_food_cost": 150,
                    "source_url": None,
                }
            ],
        },
        {
            "title": "Day 2 - Architecture",
            "activities": [
                {
                    "place_name": "Historical Site B",
                    "description": "Explore architectural features.",
                    "estimated_entry_cost": 200,
                    "estimated_transport_cost": 100,
                    "estimated_food_cost": 200,
                    "source_url": None,
                }
            ],
        },
    ]


def test_build_itinerary_response(sample_request, sample_daily_plans):
    result = build_itinerary_response(sample_request, sample_daily_plans)

    assert result.destination == "Bhopal"
    assert result.days == 2
    assert len(result.itinerary) == 2
    assert result.estimated_total_cost == 800
    assert result.budget == 3000
    assert result.within_budget is True
    assert result.remaining_budget == 2200


def test_day_costs_are_calculated_correctly(
    sample_request, sample_daily_plans
):
    result = build_itinerary_response(sample_request, sample_daily_plans)

    assert result.itinerary[0].estimated_cost == 300
    assert result.itinerary[1].estimated_cost == 500


def test_assumptions_are_preserved(sample_request, sample_daily_plans):
    assumptions = ["Entry fees have not been independently verified."]

    result = build_itinerary_response(
        sample_request,
        sample_daily_plans,
        assumptions=assumptions,
    )

    assert result.assumptions == assumptions


def test_wrong_number_of_daily_plans_is_rejected(sample_request):
    with pytest.raises(ValueError, match="Expected 2 daily plans"):
        build_itinerary_response(
            sample_request,
            daily_plans=[
                {
                    "title": "Only one day",
                    "activities": [],
                }
            ],
        )


def test_negative_activity_cost_is_rejected(
    sample_request, sample_daily_plans
):
    sample_daily_plans[0]["activities"][0]["estimated_entry_cost"] = -10

    with pytest.raises(ValueError):
        build_itinerary_response(sample_request, sample_daily_plans)


def test_over_budget_itinerary_is_reported():
    request = ItineraryRequest(
        destination="Delhi",
        budget=100,
        days=1,
    )
    daily_plans = [
        {
            "title": "Monuments",
            "activities": [
                {
                    "place_name": "Historical Site",
                    "description": "Visit a historical site.",
                    "estimated_entry_cost": 200,
                    "estimated_transport_cost": 0,
                    "estimated_food_cost": 0,
                    "source_url": None,
                }
            ],
        }
    ]

    result = build_itinerary_response(request, daily_plans)

    assert result.within_budget is False
    assert result.remaining_budget == -100
    assert "exceeds" in result.message.lower()


def test_empty_activities_are_allowed(sample_request):
    daily_plans = [
        {"title": "Day 1", "activities": []},
        {"title": "Day 2", "activities": []},
    ]

    result = build_itinerary_response(sample_request, daily_plans)

    assert result.estimated_total_cost == 0
    assert result.within_budget is True
