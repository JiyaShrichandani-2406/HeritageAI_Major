
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
    get_unknown_cost_fields,
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
                "title": daily_plan.get(
                    "title", "Heritage activities"
                ),
                "activities": [
                    activity.model_dump()
                    for activity in activities
                ],
            }
        )

    # Optimize the itinerary against the requested budget.
    optimization = optimize_itinerary(
        itinerary=validated_plans,
        budget=request.budget,
        include_food=request.include_food,
        include_transport=request.include_transport,
    )

    optimized_plans = optimization["itinerary"]
    itinerary_days: list[ItineraryDay] = []

    # Check whether any included costs are unknown.
    final_assumptions = list(assumptions or [])
    has_unknown_costs = False

    for daily_plan in optimized_plans:
        for activity in daily_plan.get("activities", []):
            unknown_fields = get_unknown_cost_fields(
                activity,
                include_food=request.include_food,
                include_transport=request.include_transport,
            )

            if unknown_fields:
                has_unknown_costs = True
                place_name = activity.get(
                    "place_name", "Unknown place"
                )

                for field in unknown_fields:
                    assumption = (
                        f"{place_name}: {field} is UNKNOWN; "
                        "the estimated total may be incomplete."
                    )

                    if assumption not in final_assumptions:
                        final_assumptions.append(assumption)

    # Preserve unknown-cost warnings supplied by the AI.
    if any(
        "UNKNOWN" in assumption.upper()
        for assumption in final_assumptions
    ):
        has_unknown_costs = True

    # Calculate each day's estimated cost.
    for day_number, daily_plan in enumerate(
        optimized_plans, start=1
    ):
        activities = [
            ItineraryActivity(**activity)
            for activity in daily_plan.get("activities", [])
        ]

        activity_data = [
            activity.model_dump()
            for activity in activities
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

    # Calculate the total estimated cost.
    total_cost = round(
        sum(day.estimated_cost for day in itinerary_days),
        2,
    )

    budget_result = check_budget(
        total_cost=total_cost,
        budget=request.budget,
    )

    # Record excluded costs in the assumptions.
    if not request.include_food:
        final_assumptions.append(
            "Food costs are excluded from the estimated total."
        )

    if not request.include_transport:
        final_assumptions.append(
            "Local transport costs are excluded from the estimated total."
        )

    # Record activities removed during budget optimization.
    if optimization["removed_activities"]:
        final_assumptions.append(
            f"Budget optimization removed "
            f"{len(optimization['removed_activities'])} activity or "
            "activities to reduce estimated costs."
        )

       # Select the message based on budget and cost certainty.
    if not budget_result["within_budget"]:
        if has_unknown_costs:
             message = (
            "The known estimated costs exceed the available budget, "
            "and some costs are unknown. The displayed total may be "
            "incomplete, so budget compliance is not fully verified."
        )
        else:
            message = (
                "The itinerary exceeds the available budget after "
                "optimization. Consider increasing the budget or changing "
                "the trip requirements."
            )
    elif has_unknown_costs:
        message = (
            "Itinerary generated, but some costs are unknown. "
            "Any displayed total is incomplete and must not be treated "
            "as the actual trip cost. Budget compliance is not verified."
        )
    else:
        message = (
            "Itinerary generated within the available budget, "
            "based on estimated costs."
        )
    # Build the final response.
    return ItineraryResponse(
        destination=request.destination,
        days=request.days,
        itinerary=itinerary_days,
        estimated_total_cost=budget_result["estimated_total_cost"],
        budget=budget_result["budget"],
        within_budget=(
            budget_result["within_budget"]
            if not has_unknown_costs
            else False
        ),
        remaining_budget=budget_result["remaining_budget"],
        assumptions=list(dict.fromkeys(final_assumptions)),
        message=message,
    )
