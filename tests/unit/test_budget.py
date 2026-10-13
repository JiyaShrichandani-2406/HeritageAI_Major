
import pytest

from backend.app.services.budget_service import (
    calculate_activity_cost,
    calculate_day_cost,
    calculate_itinerary_cost,
    check_budget,
)


def test_calculate_activity_cost():
    activity = {
        "estimated_entry_cost": 100,
        "estimated_transport_cost": 50,
        "estimated_food_cost": 150,
    }

    assert calculate_activity_cost(activity) == 300.0


def test_missing_cost_fields_default_to_zero():
    activity = {
        "estimated_entry_cost": 100,
    }

    assert calculate_activity_cost(activity) == 100.0


def test_calculate_day_cost():
    activities = [
        {
            "estimated_entry_cost": 100,
            "estimated_transport_cost": 50,
            "estimated_food_cost": 0,
        },
        {
            "estimated_entry_cost": 200,
            "estimated_transport_cost": 0,
            "estimated_food_cost": 100,
        },
    ]

    assert calculate_day_cost(activities) == 450.0


def test_calculate_itinerary_cost():
    itinerary = [
        {
            "activities": [
                {
                    "estimated_entry_cost": 100,
                    "estimated_transport_cost": 50,
                    "estimated_food_cost": 50,
                }
            ]
        },
        {
            "activities": [
                {
                    "estimated_entry_cost": 200,
                    "estimated_transport_cost": 100,
                    "estimated_food_cost": 100,
                }
            ]
        },
    ]

    assert calculate_itinerary_cost(itinerary) == 600.0


def test_check_budget_within_budget():
    result = check_budget(total_cost=1500, budget=2000)

    assert result["estimated_total_cost"] == 1500.0
    assert result["within_budget"] is True
    assert result["remaining_budget"] == 500.0


def test_check_budget_exceeded():
    result = check_budget(total_cost=2500, budget=2000)

    assert result["within_budget"] is False
    assert result["remaining_budget"] == -500.0


def test_negative_activity_cost_is_rejected():
    activity = {
        "estimated_entry_cost": -100,
    }

    with pytest.raises(ValueError):
        calculate_activity_cost(activity)


def test_string_activity_cost_is_rejected():
    activity = {
        "estimated_entry_cost": "100",
    }

    with pytest.raises(ValueError):
        calculate_activity_cost(activity)


def test_zero_budget_is_rejected():
    with pytest.raises(ValueError):
        check_budget(total_cost=100, budget=0)


def test_optimize_itinerary_removes_high_cost_activity_first():
    from backend.app.services.budget_service import optimize_itinerary

    itinerary = [
        {
            "title": "Day 1",
            "activities": [
                {
                    "place_name": "High Cost Site",
                    "estimated_entry_cost": 100,
                    "estimated_transport_cost": 0,
                    "estimated_food_cost": 0,
                },
                {
                    "place_name": "High Cost Site",
                    "estimated_entry_cost": 500,
                    "estimated_transport_cost": 0,
                    "estimated_food_cost": 0,
                },
            ],
        }
    ]

    result = optimize_itinerary(itinerary, budget=500)


    assert result["within_budget"] is True
    assert result["estimated_total_cost"] == 100
    assert len(result["removed_activities"]) == 1
    assert result["removed_activities"][0]["estimated_entry_cost"] == 500



def test_optimize_itinerary_keeps_days_when_activities_removed():
    from backend.app.services.budget_service import optimize_itinerary

    itinerary = [
        {
            "title": "Day 1",
            "activities": [
                {
                    "place_name": "Site A",
                    "estimated_entry_cost": 500,
                }
            ],
        },
        {
            "title": "Day 2",
            "activities": [
                {
                    "place_name": "Site B",
                    "estimated_entry_cost": 500,
                }
            ],
        },
    ]

    result = optimize_itinerary(itinerary, budget=100)


  
    assert len(result["itinerary"]) == 2
    assert result["within_budget"] is False
    assert result["estimated_total_cost"] == 1000
    assert all(
        len(day["activities"]) == 1
        for day in result["itinerary"]
    )
    assert result["removed_activities"] == []