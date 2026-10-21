
from typing import Any

from backend.app.schemas.itinerary import (
    ItineraryActivity,
    ItineraryDay,
    ItineraryRequest,
    ItineraryResponse,
)
from backend.app.schemas.route import TransportOptionResponse
from backend.app.schemas.service import VisitorServiceResponse
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
    transport_options: list[dict[str, Any]] | None = None,
    visitor_services: list[dict[str, Any]] | None = None,
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
        activity_payloads = daily_plan.get("activities", [])
        if not activity_payloads:
            raise ValueError(
                "Each itinerary day must contain at least one activity."
            )
        if len(activity_payloads) > 4:
            raise ValueError(
                "Each itinerary day may contain at most four activities."
            )

        activities = [
            ItineraryActivity(**activity)
            for activity in activity_payloads
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

    # Cost estimates are useful for planning but do not establish budget
    # compliance; only verified costs contribute to the known subtotal.
    final_assumptions = list(assumptions or [])
    has_unknown_costs = False
    has_estimated_costs = False

    cost_labels = {
        "estimated_entry_cost": "entry fee",
        "estimated_transport_cost": "transport cost",
        "estimated_food_cost": "food cost",
    }
    uncertain_costs: dict[str, dict[str, set[str]]] = {}

    for daily_plan in optimized_plans:
        for activity in daily_plan.get("activities", []):
            place_name = activity.get("place_name", "Unknown place")
            cost_fields = {
                "estimated_entry_cost": True,
                "estimated_transport_cost": request.include_transport,
                "estimated_food_cost": request.include_food,
            }

            for field, included in cost_fields.items():
                if not included:
                    continue

                status = activity.get(
                    {
                        "estimated_entry_cost": "entry_cost_status",
                        "estimated_transport_cost": "transport_cost_status",
                        "estimated_food_cost": "food_cost_status",
                    }[field]
                )
                if status == "unknown":
                    has_unknown_costs = True
                elif status == "estimated":
                    has_estimated_costs = True
                else:
                    continue

                status_costs = uncertain_costs.setdefault(
                    place_name, {"unknown": set(), "estimated": set()}
                )
                status_costs[status].add(cost_labels[field])

    # Model-generated cost assumptions duplicate the deterministic summary.
    final_assumptions = [
        assumption
        for assumption in final_assumptions
        if not (
            "cost" in assumption.casefold()
            and any(
                marker in assumption.casefold()
                for marker in ("unknown", "estimate", "unverified")
            )
        )
    ]
    for place_name, statuses in uncertain_costs.items():
        details = []
        for cost_status in ("estimated", "unknown"):
            labels = sorted(statuses[cost_status])
            if labels:
                details.append(
                    f"{', '.join(labels)} {cost_status}"
                )
        final_assumptions.append(f"{place_name}: {'; '.join(details)}.")

    # Calculate each day's estimated cost.
    planning_total_cost = 0.0
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
        planning_total_cost += day_cost
        day_has_unknown_costs = any(
            get_unknown_cost_fields(
                activity,
                include_food=request.include_food,
                include_transport=request.include_transport,
            )
            for activity in activity_data
        )

        itinerary_days.append(
            ItineraryDay(
                day=day_number,
                title=daily_plan["title"],
                activities=activities,
                estimated_cost=(
                    None if day_has_unknown_costs else day_cost
                ),
            )
        )

    # Calculate the total estimated cost.
    total_cost = round(planning_total_cost, 2)

    budget_result = check_budget(
        total_cost=total_cost,
        budget=request.budget,
    )

    verified_cost_subtotal = round(
        sum(
            float(activity[field] or 0)
            for daily_plan in optimized_plans
            for activity in daily_plan.get("activities", [])
            for field, status_field in (
                ("estimated_entry_cost", "entry_cost_status"),
                ("estimated_transport_cost", "transport_cost_status"),
                ("estimated_food_cost", "food_cost_status"),
            )
            if activity.get(status_field) == "verified"
            and (
                field != "estimated_food_cost" or request.include_food
            )
            and (
                field != "estimated_transport_cost"
                or request.include_transport
            )
        ),
        2,
    )
    incomplete_costs = has_unknown_costs or has_estimated_costs
    verified_costs_exceed_budget = (
        verified_cost_subtotal > request.budget
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

    if transport_options or visitor_services:
        final_assumptions.append(
            "Listed transport options and visitor services are informational; "
            "their costs are not included in the itinerary total."
        )

    # Record activities removed during budget optimization.
    if optimization["removed_activities"]:
        final_assumptions.append(
            f"Budget optimization removed "
            f"{len(optimization['removed_activities'])} activity or "
            "activities to reduce estimated costs."
        )

    # Select the message based on budget and cost certainty.
    if verified_costs_exceed_budget:
        if incomplete_costs:
            message = (
                "Verified costs alone exceed the available budget, "
                "and other costs are estimated or unknown."
            )
        else:
            message = (
                "Verified itinerary costs exceed the available budget."
            )
    elif incomplete_costs:
        message = (
            "Itinerary generated with estimated or unknown costs. "
            "The displayed total is an estimate and budget compliance "
            "is not verified."
        )
    else:
        message = (
            "Itinerary generated within the available budget, "
            "based on verified costs."
        )

    # Build the final response.
    return ItineraryResponse(
        destination=request.destination,
        days=request.days,
        itinerary=itinerary_days,
        transport_options=[
            TransportOptionResponse(**option)
            for option in (transport_options or [])
        ],
        visitor_services=[
            VisitorServiceResponse(**service)
            for service in (visitor_services or [])
        ],
        budget=budget_result["budget"],
        known_cost_subtotal=verified_cost_subtotal,
        estimated_total_cost=(
            None
            if has_unknown_costs
            else budget_result["estimated_total_cost"]
        ),
        within_budget=(
            False
            if verified_costs_exceed_budget
            else None
            if incomplete_costs
            else True
        ),
        remaining_budget=(
            None
            if incomplete_costs
            else budget_result["remaining_budget"]
        ),
        assumptions=list(dict.fromkeys(final_assumptions)),
        message=message,
    )
