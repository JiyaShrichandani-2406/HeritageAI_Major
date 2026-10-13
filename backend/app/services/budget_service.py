
from typing import Any


def calculate_activity_cost(
    activity: dict[str, Any],
    include_food: bool = True,
    include_transport: bool = True,
) -> float:
    """Calculate the estimated cost of one activity."""

    cost_fields = {
        "estimated_entry_cost": True,
        "estimated_transport_cost": include_transport,
        "estimated_food_cost": include_food,
    }

    total = 0.0

    for field, should_include in cost_fields.items():
        value = activity.get(field, 0)

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a number.")

        if value < 0:
            raise ValueError(f"{field} cannot be negative.")

        if should_include:
            total += float(value)

    return round(total, 2)


def calculate_day_cost(
    activities: list[dict[str, Any]],
    include_food: bool = True,
    include_transport: bool = True,
) -> float:
    """Calculate the total estimated cost of a day's activities."""

    if not isinstance(activities, list):
        raise ValueError("Activities must be provided as a list.")

    total = sum(
        calculate_activity_cost(
            activity,
            include_food=include_food,
            include_transport=include_transport,
        )
        for activity in activities
    )

    return round(total, 2)


def calculate_itinerary_cost(
    itinerary: list[dict[str, Any]],
    include_food: bool = True,
    include_transport: bool = True,
) -> float:
    """Calculate the estimated cost across all itinerary days."""

    if not isinstance(itinerary, list):
        raise ValueError("Itinerary must be provided as a list.")

    total = 0.0

    for day in itinerary:
        activities = day.get("activities", [])

        total += calculate_day_cost(
            activities,
            include_food=include_food,
            include_transport=include_transport,
        )

    return round(total, 2)


def check_budget(total_cost: float, budget: float) -> dict[str, Any]:
    """Check whether the estimated trip cost fits the available budget."""

    for name, value in (("total_cost", total_cost), ("budget", budget)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number.")

        if value < 0:
            raise ValueError(f"{name} cannot be negative.")

    if budget == 0:
        raise ValueError("Budget must be greater than zero.")

    total_cost = round(float(total_cost), 2)
    budget = round(float(budget), 2)
    remaining = round(budget - total_cost, 2)

    return {
        "estimated_total_cost": total_cost,
        "budget": budget,
        "within_budget": total_cost <= budget,
        "remaining_budget": remaining,
    }



def optimize_itinerary(
    itinerary: list[dict[str, Any]],
    budget: float,
    include_food: bool = True,
    include_transport: bool = True,
) -> dict[str, Any]:
    """Reduce itinerary costs while preserving at least one activity per
    day that originally contained activities.
    """

    if not isinstance(itinerary, list):
        raise ValueError("Itinerary must be provided as a list.")

    if isinstance(budget, bool) or not isinstance(budget, (int, float)):
        raise ValueError("Budget must be a number.")

    if budget <= 0:
        raise ValueError("Budget must be greater than zero.")

    # Create copies so the original itinerary is not modified.
    optimized = [
        {
            **day,
            "activities": [
                dict(activity)
                for activity in day.get("activities", [])
            ],
        }
        for day in itinerary
    ]

    def total_cost() -> float:
        return calculate_itinerary_cost(
            optimized,
            include_food=include_food,
            include_transport=include_transport,
        )

    removed_activities = []

    while total_cost() > budget:
        candidates = []

        for day_index, day in enumerate(optimized):
            activities = day["activities"]

            # Do not remove the last activity from a day.
            if len(activities) <= 1:
                continue

            for activity_index, activity in enumerate(activities):
                cost = calculate_activity_cost(
                    activity,
                    include_food=include_food,
                    include_transport=include_transport,
                )
                candidates.append(
                    (cost, day_index, activity_index)
                )

        # Stop if no more activities can be removed safely.
        if not candidates:
            break

        # Remove the highest-cost activity first.
        _, day_index, activity_index = max(candidates)

        removed = optimized[day_index]["activities"].pop(
            activity_index
        )
        removed_activities.append(removed)

    final_cost = total_cost()
    budget_result = check_budget(final_cost, budget)

    return {
        "itinerary": optimized,
        "estimated_total_cost": budget_result["estimated_total_cost"],
        "budget": budget_result["budget"],
        "within_budget": budget_result["within_budget"],
        "remaining_budget": budget_result["remaining_budget"],
        "removed_activities": removed_activities,
    }
