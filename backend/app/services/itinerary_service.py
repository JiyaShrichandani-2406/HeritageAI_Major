
from typing import Any

from backend.app.schemas.itinerary import (
    ItineraryActivity,
    ItineraryDay,
    ItineraryRequest,
    ItineraryResponse,
)
from backend.app.services.budget_service import (
    calculate_day_cost,
    check_budget,
    optimize_itinerary,
)


def build_itinerary_response(
    request: ItineraryRequest,
    daily_plans: list[dict[str, Any]],
    assumptions: list[str] | None = None,
) -> ItineraryResponse:
    """Build, optimize, and validate a budget-aware itinerary response."""

    if len(daily_plans) != request.days:
        raise ValueError(
            f"Expected {request.days} daily plans, "
            f"but received {len(daily_plans)}."
        )

    # Validate AI-generated activities before calculating costs.
    validated_plans = []

    for daily_plan in daily_plans:
        activities = [
            ItineraryActivity(**activity)
            for activity in daily_plan.get("activities", [])
        ]

        validated_plans.append(
            {
                "title": daily_plan.get("title", "Heritage activities"),
                "activities": [
                    activity.model_dump() for activity in activities
                ],
            }
        )

    # Optimize the itinerary if its estimated costs exceed the budget.
    optimization = optimize_itinerary(
        itinerary=validated_plans,
        budget=request.budget,
        include_food=request.include_food,
        include_transport=request.include_transport,
    )

    optimized_plans = optimization["itinerary"]
    itinerary_days: list[ItineraryDay] = []

    # Recalculate each day's cost after optimization.
    for day_number, daily_plan in enumerate(optimized_plans, start=1):
        activities = [
            ItineraryActivity(**activity)
            for activity in daily_plan.get("activities", [])
        ]

        activity_data = [
            activity.model_dump() for activity in activities
        ]

        day_cost = calculate_day_cost(
            activity_data,
            include_food=request.include_food,
            include_transport=request.include_transport,
        )

        itinerary_days.append(
            ItineraryDay(
                day=day_number,
                title=daily_plan["title"],
                activities=activities,
                estimated_cost=day_cost,
            )
        )

    total_cost = round(
        sum(day.estimated_cost for day in itinerary_days),
        2,
    )

    budget_result = check_budget(
        total_cost=total_cost,
        budget=request.budget,
    )

    final_assumptions = list(assumptions or [])

    if not request.include_food:
        final_assumptions.append(
            "Food costs are excluded from the estimated total."
        )

    if not request.include_transport:
        final_assumptions.append(
            "Local transport costs are excluded from the estimated total."
        )

    if optimization["removed_activities"]:
        final_assumptions.append(
            f"Budget optimization removed "
            f"{len(optimization['removed_activities'])} activity or "
            "activities to reduce estimated costs."
        )

    if budget_result["within_budget"]:
        message = "Itinerary generated within the available budget."
    else:
        message = (
            "The itinerary still exceeds the available budget after "
            "optimization. Consider increasing the budget or changing "
            "the trip requirements."
        )

    return ItineraryResponse(
        destination=request.destination,
        days=request.days,
        itinerary=itinerary_days,
        estimated_total_cost=budget_result["estimated_total_cost"],
        budget=budget_result["budget"],
        within_budget=budget_result["within_budget"],
        remaining_budget=budget_result["remaining_budget"],
        assumptions=final_assumptions,
        message=message,
    )
