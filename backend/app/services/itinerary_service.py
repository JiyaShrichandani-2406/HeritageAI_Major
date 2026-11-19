
from typing import Any

from backend.app.repositories.location_repository import LocationRepository
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
    calculate_itinerary_cost,
    check_budget,
    get_unknown_cost_fields,
    optimize_itinerary,
)
from backend.app.services.transport_service import select_transport_option


def _reapply_local_transport_estimates(
    itinerary: list[dict[str, Any]],
    request: ItineraryRequest,
    transport_options: list[dict[str, Any]],
) -> None:
    """Recalculate sourced leg estimates after budget trimming changes stop order."""
    locations = LocationRepository()
    routes_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for option in transport_options:
        routes_by_pair.setdefault(
            (option["origin_id"], option["destination_id"]), []
        ).append(option)

    start_place = None
    if request.itinerary_mode == "place_to_place":
        if request.origin_id:
            start_place = next(
                (
                    place
                    for place in locations.places()
                    if place["id"] == request.origin_id
                ),
                None,
            )
        else:
            start_place = locations.find_place(request.origin or "")
    start_place_id = start_place["id"] if start_place else None
    start_city_id = None
    if request.itinerary_mode == "city_to_city":
        start_city = (
            next(
                (
                    city
                    for city in locations.cities()
                    if city["id"] == request.origin_id
                ),
                None,
            )
            if request.origin_id
            else locations.find_city(request.origin or "")
        )
        start_city_id = start_city["id"] if start_city else None
    for day_index, day in enumerate(itinerary):
        previous_place_id = start_place_id if day_index == 0 else None
        for activity_index, activity in enumerate(
            day.get("activities", [])
        ):
            place = locations.find_place(activity["place_name"])
            activity["estimated_transport_cost"] = None
            activity["transport_cost_status"] = "unknown"
            activity["estimated_travel_duration_minutes"] = None
            activity["travel_duration_status"] = "unknown"
            activity["transport_type"] = None
            activity["transport_source_url"] = None
            activity["transport_notes"] = None

            if not place:
                previous_place_id = None
                continue

            city_origin_leg = (
                day_index == 0
                and activity_index == 0
                and start_city_id is not None
            )
            if city_origin_leg:
                route = select_transport_option(
                    routes_by_pair.get(
                        (start_city_id, place["city_id"]), []
                    ),
                    request.travel_style,
                )
                if route:
                    if request.include_transport:
                        activity["estimated_transport_cost"] = route[
                            "estimated_cost"
                        ]
                        activity["transport_cost_status"] = route[
                            "cost_status"
                        ]
                    activity["estimated_travel_duration_minutes"] = route[
                        "estimated_duration_minutes"
                    ]
                    activity["travel_duration_status"] = route[
                        "duration_status"
                    ]
                    activity["transport_type"] = route["transport_type"]
                    activity["transport_source_url"] = route["source_url"]
                    activity["transport_notes"] = route.get("notes", "")
            elif previous_place_id and previous_place_id != place["id"]:
                route = select_transport_option(
                    routes_by_pair.get((previous_place_id, place["id"]), []),
                    request.travel_style,
                )
                if route:
                    if request.include_transport:
                        activity["estimated_transport_cost"] = route[
                            "estimated_cost"
                        ]
                        activity["transport_cost_status"] = route[
                            "cost_status"
                        ]
                    activity["estimated_travel_duration_minutes"] = route[
                        "estimated_duration_minutes"
                    ]
                    activity["travel_duration_status"] = route[
                        "duration_status"
                    ]
                    activity["transport_type"] = route["transport_type"]
                    activity["transport_source_url"] = route["source_url"]
                    activity["transport_notes"] = route.get("notes", "")

            previous_place_id = place["id"]


def build_itinerary_response(
    request: ItineraryRequest,
    daily_plans: list[dict[str, Any]],
    assumptions: list[str] | None = None,
    transport_options: list[dict[str, Any]] | None = None,
    visitor_services: list[dict[str, Any]] | None = None,
    local_transport_options: list[dict[str, Any]] | None = None,
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
    protected_place_names = set()
    if request.itinerary_mode == "place_to_place":
        locations = LocationRepository()
        for location_id, location_name in (
            (request.origin_id, request.origin),
            (request.destination_id, request.destination),
        ):
            place = (
                next(
                    (
                        candidate
                        for candidate in locations.places()
                        if candidate["id"] == location_id
                    ),
                    None,
                )
                if location_id
                else locations.find_place(location_name or "")
            )
            if place and place.get("category") != "transit_stop":
                protected_place_names.add(place["name"])

    remaining_plans = validated_plans
    removed_activities = []
    max_optimization_rounds = sum(
        len(day["activities"]) for day in validated_plans
    ) + 1
    for _ in range(max_optimization_rounds):
        optimization = optimize_itinerary(
            itinerary=remaining_plans,
            budget=request.budget,
            include_food=request.include_food,
            include_transport=request.include_transport,
            include_guides=request.include_guides,
            include_parking=request.include_parking,
            protected_place_names=protected_place_names,
        )
        remaining_plans = optimization["itinerary"]
        removed_activities.extend(optimization["removed_activities"])
        if local_transport_options is None:
            break
        _reapply_local_transport_estimates(
            remaining_plans,
            request,
            [
                *(local_transport_options or []),
                *(transport_options or []),
            ],
        )
        if (
            calculate_itinerary_cost(
                remaining_plans,
                include_food=request.include_food,
                include_transport=request.include_transport,
                include_guides=request.include_guides,
                include_parking=request.include_parking,
            )
            <= request.budget
            or not optimization["removed_activities"]
        ):
            break
    optimization["itinerary"] = remaining_plans
    optimization["removed_activities"] = removed_activities

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
        "estimated_guide_cost": "guide cost",
        "estimated_parking_cost": "parking cost",
    }
    uncertain_costs: dict[str, dict[str, set[str]]] = {}

    for daily_plan in optimized_plans:
        for activity in daily_plan.get("activities", []):
            place_name = activity.get("place_name", "Unknown place")
            cost_fields = {
                "estimated_entry_cost": True,
                "estimated_transport_cost": request.include_transport,
                "estimated_food_cost": request.include_food,
                "estimated_guide_cost": request.include_guides,
                "estimated_parking_cost": request.include_parking,
            }
            status_fields = {
                "estimated_entry_cost": "entry_cost_status",
                "estimated_transport_cost": "transport_cost_status",
                "estimated_food_cost": "food_cost_status",
                "estimated_guide_cost": "guide_cost_status",
                "estimated_parking_cost": "parking_cost_status",
            }

            for field, included in cost_fields.items():
                if not included:
                    continue

                status = activity.get(status_fields[field])
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
            include_guides=request.include_guides,
            include_parking=request.include_parking,
        )
        planning_total_cost += day_cost
        day_has_unknown_costs = any(
            get_unknown_cost_fields(
                activity,
                include_food=request.include_food,
                include_transport=request.include_transport,
                include_guides=request.include_guides,
                include_parking=request.include_parking,
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
    unknown_cost_count = sum(
        len(
            get_unknown_cost_fields(
                activity,
                include_food=request.include_food,
                include_transport=request.include_transport,
                include_guides=request.include_guides,
                include_parking=request.include_parking,
            )
        )
        for daily_plan in optimized_plans
        for activity in daily_plan.get("activities", [])
    )

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
                ("estimated_guide_cost", "guide_cost_status"),
                ("estimated_parking_cost", "parking_cost_status"),
            )
            if activity.get(status_field) == "verified"
            and (
                field != "estimated_food_cost" or request.include_food
            )
            and (
                field != "estimated_transport_cost"
                or request.include_transport
            )
            and (
                field != "estimated_guide_cost"
                or request.include_guides
            )
            and (
                field != "estimated_parking_cost"
                or request.include_parking
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

    if transport_options:
        final_assumptions.append(
            "Matching sourced transport costs are included only for selected "
            "and supported itinerary legs."
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
        if total_cost > request.budget:
            message = (
                f"Priced costs total INR {total_cost:.2f}, above the "
                "available budget; unknown or estimated costs mean budget "
                "compliance is not verified."
            )
        else:
            message = (
                "Priced costs currently fit the budget, but estimated or "
                "unknown amounts mean budget compliance is not verified."
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
        priced_cost_subtotal=total_cost,
        unknown_cost_count=unknown_cost_count,
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
