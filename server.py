"""
Meal Tracking MCP Server

An MCP server to track meal times (breakfast, lunch, dinner).
Users can log when they start and finish a meal, and retrieve their meal history.
"""

import os
from datetime import datetime, timezone
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
    now = datetime.now(timezone.utc)

    supabase = get_supabase()
    supabase.table("meals").insert({
        "user_id": user_id,
        "type": meal_type,
        "started_at": now.isoformat(),
    }).execute()

    return f"Started {meal_type} at {now.strftime('%H:%M')} UTC"


@mcp.tool
def end_meal(meal_type: MealType, ctx: Context) -> str:
    """
    Log the end of a meal.

    Args:
        meal_type: Type of meal - breakfast, lunch, or dinner
    """
    user_id = get_user_id(ctx)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    supabase = get_supabase()

    # Find the most recent meal of this type today that hasn't ended
    result = (
        supabase.table("meals")
        .select("id")
        .eq("user_id", user_id)
        .eq("type", meal_type)
        .gte("started_at", today_start.isoformat())
        .is_("ended_at", "null")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        return f"No active {meal_type} found for today. Did you forget to start it?"

    # Update the meal with end time
    meal_id = result.data[0]["id"]
    supabase.table("meals").update({
        "ended_at": now.isoformat()
    }).eq("id", meal_id).execute()

    return f"Finished {meal_type} at {now.strftime('%H:%M')} UTC"


@mcp.tool
def get_meals_today(ctx: Context) -> str:
    """Get all meals logged for today."""
    user_id = get_user_id(ctx)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    supabase = get_supabase()
    result = (
        supabase.table("meals")
        .select("*")
        .eq("user_id", user_id)
        .gte("started_at", today_start.isoformat())
        .order("started_at")
        .execute()
    )

    if not result.data:
        return "No meals logged today."

    lines = [f"Meals for {now.strftime('%Y-%m-%d')}:"]
    for meal in result.data:
        started = datetime.fromisoformat(meal["started_at"].replace("Z", "+00:00"))
        start_str = started.strftime("%H:%M")
        if meal["ended_at"]:
            ended = datetime.fromisoformat(meal["ended_at"].replace("Z", "+00:00"))
            end_str = ended.strftime("%H:%M")
        else:
            end_str = "ongoing"
        lines.append(f"  - {meal['type'].capitalize()}: {start_str} - {end_str} UTC")

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
    result = (
        supabase.table("meals")
        .select("*")
        .eq("user_id", user_id)
        .order("started_at", desc=True)
        .execute()
    )

    if not result.data:
        return "No meal history found."

    # Group meals by date
    meals_by_date: dict[str, list] = {}
    for meal in result.data:
        started = datetime.fromisoformat(meal["started_at"].replace("Z", "+00:00"))
        date = started.strftime("%Y-%m-%d")
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
            started = datetime.fromisoformat(meal["started_at"].replace("Z", "+00:00"))
            start_str = started.strftime("%H:%M")
            if meal["ended_at"]:
                ended = datetime.fromisoformat(meal["ended_at"].replace("Z", "+00:00"))
                end_str = ended.strftime("%H:%M")
            else:
                end_str = "ongoing"
            lines.append(f"  - {meal['type'].capitalize()}: {start_str} - {end_str} UTC")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
