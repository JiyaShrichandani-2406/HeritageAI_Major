
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
                    "entry_cost_status": "estimated",
                    "estimated_transport_cost": 0,
                    "transport_cost_status": "verified",
                    "estimated_food_cost": 0,
                    "food_cost_status": "verified",
                    "source_url": None,
                }
            ],
        }
    ]

    result = build_itinerary_response(request, daily_plans)

    assert result.within_budget is False
    assert result.remaining_budget == -100
    assert "exceed" in result.message.lower()


def test_empty_activities_are_rejected(sample_request):
    daily_plans = [
        {
            "title": "Day 1",
            "activities": [
                {
                    "place_name": "Site A",
                    "description": "Visit the heritage site.",
                    "estimated_entry_cost": 100,
                }
            ],
        },
        {"title": "Day 2", "activities": []},
    ]

    with pytest.raises(
        ValueError,
        match="Each itinerary day must contain at least one activity",
    ):
        build_itinerary_response(sample_request, daily_plans)

def test_unknown_costs_do_not_confirm_budget_compliance():
    request = ItineraryRequest(
        destination="Agra",
        budget=5000,
        days=1,
    )

    daily_plans = [
        {
            "title": "Day 1 - Heritage Sites",
            "activities": [
                {
                    "place_name": "Taj Mahal",
                    "description": "Explore the monument.",
                    "estimated_entry_cost": 0,
                    "entry_cost_status": "unknown",
                    "estimated_transport_cost": 0,
                    "transport_cost_status": "unknown",
                    "estimated_food_cost": 0,
                    "food_cost_status": "unknown",
                    "source_url": None,
                }
            ],
        }
    ]

    result = build_itinerary_response(request, daily_plans)

    assert result.within_budget is None
    assert result.known_cost_subtotal == 0
    assert result.estimated_total_cost is None
    assert result.remaining_budget is None
    assert "not verified" in result.message.lower()
    assert any(
        "unknown" in assumption.lower()
        for assumption in result.assumptions
    )
