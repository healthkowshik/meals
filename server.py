"""
Meal Tracking MCP Server

An MCP server to track meal times (breakfast, lunch, dinner).
Users can log when they start and finish a meal, and retrieve their meal history.
"""

import os
from datetime import datetime
from typing import Literal

from fastmcp import FastMCP, Context
from supabase import create_client, Client

mcp = FastMCP("Meals Tracker")

# Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

MealType = Literal["breakfast", "lunch", "dinner"]


def get_supabase() -> Client:
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables required")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user_id(ctx: Context) -> str:
    """Get user ID from context, fallback to client_id."""
    return ctx.client_id or "anonymous"


@mcp.tool
def start_meal(meal_type: MealType, ctx: Context) -> str:
    """
    Log the start of a meal.

    Args:
        meal_type: Type of meal - breakfast, lunch, or dinner
    """
    user_id = get_user_id(ctx)
    now = datetime.now()

    supabase = get_supabase()
    supabase.table("meals").insert({
        "user_id": user_id,
        "type": meal_type,
        "date": now.strftime("%Y-%m-%d"),
        "start_time": now.strftime("%H:%M:%S"),
    }).execute()

    return f"Started {meal_type} at {now.strftime('%H:%M')}"


@mcp.tool
def end_meal(meal_type: MealType, ctx: Context) -> str:
    """
    Log the end of a meal.

    Args:
        meal_type: Type of meal - breakfast, lunch, or dinner
    """
    user_id = get_user_id(ctx)
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    supabase = get_supabase()

    # Find the most recent meal of this type today that hasn't ended
    result = supabase.table("meals").select("id").eq("user_id", user_id).eq("type", meal_type).eq("date", today).is_("end_time", "null").order("start_time", desc=True).limit(1).execute()

    if not result.data:
        return f"No active {meal_type} found for today. Did you forget to start it?"

    # Update the meal with end time
    meal_id = result.data[0]["id"]
    supabase.table("meals").update({
        "end_time": now.strftime("%H:%M:%S")
    }).eq("id", meal_id).execute()

    return f"Finished {meal_type} at {now.strftime('%H:%M')}"


@mcp.tool
def get_meals_today(ctx: Context) -> str:
    """Get all meals logged for today."""
    user_id = get_user_id(ctx)
    today = datetime.now().strftime("%Y-%m-%d")

    supabase = get_supabase()
    result = supabase.table("meals").select("*").eq("user_id", user_id).eq("date", today).order("start_time").execute()

    if not result.data:
        return "No meals logged today."

    lines = [f"Meals for {today}:"]
    for meal in result.data:
        start = meal["start_time"][:5]  # HH:MM
        end = meal["end_time"][:5] if meal["end_time"] else "ongoing"
        lines.append(f"  - {meal['type'].capitalize()}: {start} - {end}")

    return "\n".join(lines)


@mcp.tool
def get_meals_history(ctx: Context, days: int = 7) -> str:
    """
    Get meal history for the specified number of days.

    Args:
        days: Number of days to look back (default: 7)
    """
    user_id = get_user_id(ctx)

    supabase = get_supabase()
    result = supabase.table("meals").select("*").eq("user_id", user_id).order("date", desc=True).order("start_time").execute()

    if not result.data:
        return "No meal history found."

    # Group meals by date
    meals_by_date: dict[str, list] = {}
    for meal in result.data:
        date = meal["date"]
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
            start = meal["start_time"][:5]
            end = meal["end_time"][:5] if meal["end_time"] else "ongoing"
            lines.append(f"  - {meal['type'].capitalize()}: {start} - {end}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
