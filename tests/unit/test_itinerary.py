
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


def test_parking_inclusion_requires_a_vehicle_type():
    with pytest.raises(ValueError, match="vehicle type is required"):
        ItineraryRequest(
            destination="Agra",
            budget=5000,
            days=1,
            include_parking=True,
        )


def test_parking_vehicle_type_cannot_be_set_when_parking_is_excluded():
    with pytest.raises(ValueError, match="only be set when parking costs"):
        ItineraryRequest(
            destination="Agra",
            budget=5000,
            days=1,
            parking_vehicle_type="car_taxi",
        )


def test_budget_optimization_reapplies_city_to_city_fare_to_first_stop():
    from backend.app.services.itinerary_service import (
        _reapply_local_transport_estimates,
    )

    request = ItineraryRequest(
        itinerary_mode="city_to_city",
        origin="Delhi",
        origin_id="city-delhi",
        destination="Agra",
        destination_id="city-agra",
        budget=5000,
        days=1,
    )
    itinerary = [
        {
            "activities": [
                {
                    "place_name": "Taj Mahal",
                    "estimated_transport_cost": None,
                    "transport_cost_status": "unknown",
                }
            ]
        }
    ]

    _reapply_local_transport_estimates(
        itinerary,
        request,
        [
            {
                "id": "delhi-agra-train",
                "origin_id": "city-delhi",
                "destination_id": "city-agra",
                "estimated_cost": 500,
                "cost_status": "estimated",
                "estimated_duration_minutes": 180,
                "duration_status": "estimated",
                "transport_type": "train",
                "source_url": "https://example.com/route",
                "notes": None,
            }
        ],
    )

    activity = itinerary[0]["activities"][0]
    assert activity["estimated_transport_cost"] == 500
    assert activity["transport_cost_status"] == "estimated"
    assert activity["estimated_travel_duration_minutes"] == 180


def test_build_itinerary_response(sample_request, sample_daily_plans):
    result = build_itinerary_response(sample_request, sample_daily_plans)

    assert result.destination == "Bhopal"
    assert result.days == 2
    assert len(result.itinerary) == 2
    assert result.estimated_total_cost == 800
    assert result.budget == 3000
    assert result.within_budget is None
    assert result.remaining_budget is None
    assert result.known_cost_subtotal == 0
    assert result.priced_cost_subtotal == 800
    assert result.estimated_total_cost == 800


def test_day_costs_are_calculated_correctly(
    sample_request, sample_daily_plans
):
    result = build_itinerary_response(sample_request, sample_daily_plans)

    assert result.itinerary[0].estimated_cost == 300
    assert result.itinerary[1].estimated_cost == 500


def test_place_to_place_recalculates_legs_after_budget_removes_a_stop():
    request = ItineraryRequest(
        itinerary_mode="place_to_place",
        origin="Taj Mahal",
        origin_id="place-taj-mahal",
        destination="Chini ka Rauza",
        destination_id="place-chini-ka-rauza",
        budget=50,
        days=1,
    )
    daily_plans = [
        {
            "title": "Day 1",
            "activities": [
                {
                    "place_name": "Taj Mahal",
                    "description": "Start at selected place.",
                    "estimated_entry_cost": None,
                    "entry_cost_status": "unknown",
                },
                {
                    "place_name": "Agra Fort",
                    "description": "Visit the fort.",
                    "estimated_entry_cost": None,
                    "entry_cost_status": "unknown",
                    "estimated_transport_cost": 65,
                    "transport_cost_status": "estimated",
                },
                {
                    "place_name": "Chini ka Rauza",
                    "description": "Arrive at selected destination.",
                    "estimated_entry_cost": None,
                    "entry_cost_status": "unknown",
                },
            ],
        }
    ]

    result = build_itinerary_response(
        request,
        daily_plans,
        local_transport_options=[
            {
                "origin_id": "place-taj-mahal",
                "destination_id": "place-agra-fort",
                "transport_type": "auto-rickshaw",
                "estimated_cost": 65,
                "estimated_duration_minutes": 10,
                "duration_status": "estimated",
                "cost_status": "estimated",
                "source_url": "https://example.org/taj-to-fort",
                "notes": "",
            },
            {
                "origin_id": "place-taj-mahal",
                "destination_id": "place-chini-ka-rauza",
                "transport_type": "auto-rickshaw",
                "estimated_cost": 85,
                "estimated_duration_minutes": 15,
                "duration_status": "estimated",
                "cost_status": "estimated",
                "source_url": "https://example.org/taj-to-chini",
                "notes": "",
            },
        ],
    )

    assert [
        activity.place_name for activity in result.itinerary[0].activities
    ] == ["Taj Mahal", "Chini ka Rauza"]
    assert result.itinerary[0].activities[-1].estimated_transport_cost == 85
    assert (
        result.itinerary[0].activities[-1].estimated_travel_duration_minutes
        == 15
    )


def test_assumptions_are_preserved(sample_request, sample_daily_plans):
    assumptions = ["Entry fees have not been independently verified."]

    result = build_itinerary_response(
        sample_request,
        sample_daily_plans,
        assumptions=assumptions,
    )

    assert result.assumptions[0] == assumptions[0]
    assert len(result.assumptions) == 3


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


def test_estimated_costs_do_not_claim_budget_compliance():
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

    assert result.within_budget is None
    assert result.known_cost_subtotal == 0
    assert result.estimated_total_cost == 200
    assert result.remaining_budget is None
    assert "not verified" in result.message.lower()


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
    assert result.priced_cost_subtotal == 0
    assert result.unknown_cost_count == 3
    assert result.remaining_budget is None
    assert result.itinerary[0].estimated_cost is None
    assert "not verified" in result.message.lower()
    assert any(
        "unknown" in assumption.lower()
        for assumption in result.assumptions
    )


def test_estimated_food_cost_is_not_in_known_cost_subtotal():
    request = ItineraryRequest(
        destination="Agra",
        budget=1000,
        days=1,
    )
    daily_plans = [
        {
            "title": "Day 1",
            "activities": [
                {
                    "place_name": "Taj Mahal",
                    "description": "Explore the monument.",
                    "estimated_entry_cost": 100,
                    "entry_cost_status": "verified",
                    "estimated_transport_cost": 0,
                    "transport_cost_status": "verified",
                    "estimated_food_cost": 500,
                    "food_cost_status": "estimated",
                }
            ],
        }
    ]

    result = build_itinerary_response(request, daily_plans)

    assert result.known_cost_subtotal == 100
    assert result.priced_cost_subtotal == 600
    assert result.unknown_cost_count == 0
    assert result.estimated_total_cost == 600
    assert (
        result.itinerary[0].activities[0].estimated_food_cost
        == 500
    )
    assert result.within_budget is None
    assert result.remaining_budget is None
