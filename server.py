"""
Meal Tracking MCP Server

An MCP server to track meal times (breakfast, lunch, dinner).
Users can log when they start and finish a meal, and retrieve their meal history.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

mcp = FastMCP("Meals Tracker")

# Data storage path
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "meals.json"

MealType = Literal["breakfast", "lunch", "dinner"]


def load_data() -> dict:
    """Load meal data from JSON file."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"meals": []}


def save_data(data: dict) -> None:
    """Save meal data to JSON file."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


@mcp.tool
def start_meal(meal_type: MealType) -> str:
    """
    Log the start of a meal.

    Args:
        meal_type: Type of meal - breakfast, lunch, or dinner
    """
    data = load_data()
    now = datetime.now()

    meal_entry = {
        "type": meal_type,
        "start_datetime": now.isoformat(),
        "end_datetime": None,
    }

    data["meals"].append(meal_entry)
    save_data(data)

    return f"Started {meal_type} at {now.strftime('%H:%M')}"


@mcp.tool
def end_meal(meal_type: MealType) -> str:
    """
    Log the end of a meal.

    Args:
        meal_type: Type of meal - breakfast, lunch, or dinner
    """
    data = load_data()
    now = datetime.now()

    # Find the most recent meal of this type that hasn't ended
    for meal in reversed(data["meals"]):
        if meal["type"] == meal_type and meal["end_datetime"] is None:
            meal["end_datetime"] = now.isoformat()
            save_data(data)
            return f"Finished {meal_type} at {now.strftime('%H:%M')}"

    return f"No active {meal_type} found. Did you forget to start it?"


@mcp.tool
def get_meals_today() -> str:
    """Get all meals logged for today."""
    data = load_data()
    today = datetime.now().date()

    today_meals = [
        m for m in data["meals"]
        if datetime.fromisoformat(m["start_datetime"]).date() == today
    ]

    if not today_meals:
        return "No meals logged today."

    lines = [f"Meals for {today}:"]
    for meal in today_meals:
        start_dt = datetime.fromisoformat(meal["start_datetime"])
        start = start_dt.strftime("%H:%M")
        if meal["end_datetime"]:
            end_dt = datetime.fromisoformat(meal["end_datetime"])
            end = end_dt.strftime("%H:%M")
        else:
            end = "ongoing"
        lines.append(f"  - {meal['type'].capitalize()}: {start} - {end}")

    return "\n".join(lines)


@mcp.tool
def get_meals_history(days: int = 7) -> str:
    """
    Get meal history for the specified number of days.

    Args:
        days: Number of days to look back (default: 7)
    """
    data = load_data()

    if not data["meals"]:
        return "No meal history found."

    # Group meals by start date
    meals_by_date: dict[str, list] = {}
    for meal in data["meals"]:
        start_dt = datetime.fromisoformat(meal["start_datetime"])
        date = start_dt.strftime("%Y-%m-%d")
        if date not in meals_by_date:
            meals_by_date[date] = []
        meals_by_date[date].append(meal)

    # Get last N days with data
    sorted_dates = sorted(meals_by_date.keys(), reverse=True)[:days]

    if not sorted_dates:
        return "No meal history found."

    lines = [f"Meal history (last {days} days):"]
    for date in sorted_dates:
        lines.append(f"\n{date}:")
        for meal in meals_by_date[date]:
            start_dt = datetime.fromisoformat(meal["start_datetime"])
            start = start_dt.strftime("%H:%M")
            if meal["end_datetime"]:
                end_dt = datetime.fromisoformat(meal["end_datetime"])
                end = end_dt.strftime("%H:%M")
            else:
                end = "ongoing"
            lines.append(f"  - {meal['type'].capitalize()}: {start} - {end}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
