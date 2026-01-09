# meals

> Better Health, One Meal at a Time

An MCP (Model Context Protocol) server for tracking meal times. Log when you start and finish breakfast, lunch, and dinner, and retrieve your meal history.

## Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)

2. Run this SQL in the SQL Editor to create the `meals` table:

```sql
create table meals (
  id uuid default gen_random_uuid() primary key,
  user_id text not null,
  type text not null check (type in ('breakfast', 'lunch', 'dinner')),
  date date not null,
  start_time time not null,
  end_time time,
  created_at timestamp with time zone default now()
);

create index meals_user_id_date_idx on meals(user_id, date);
```

3. Get your credentials from Project Settings → API:
   - `SUPABASE_URL` (Project URL)
   - `SUPABASE_KEY` (anon/public key)

## Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Environment Variables

Set these before running:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
```

### Running the server

**Standard mode (stdio transport):**
```bash
source .venv/bin/activate
python server.py
```

**HTTP transport:**
```bash
source .venv/bin/activate
fastmcp run server.py:mcp --transport http --port 8000
```

### Configuring with Claude Code

Add to your Claude Code MCP configuration (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "meals": {
      "command": "/path/to/meals/.venv/bin/python",
      "args": ["/path/to/meals/server.py"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-anon-key"
      }
    }
  }
}
```

Replace `/path/to/meals` with the actual path to this project.

## Available Tools

| Tool | Description |
|------|-------------|
| `start_meal(meal_type)` | Log when you start a meal (breakfast, lunch, or dinner) |
| `end_meal(meal_type)` | Log when you finish a meal |
| `get_meals_today()` | View all meals logged today |
| `get_meals_history(days)` | View meal history for the last N days (default: 7) |

## Example Usage

Once configured, you can interact with the MCP through Claude:

- "I'm going for breakfast" → triggers `start_meal("breakfast")`
- "Back from lunch" → triggers `end_meal("lunch")`
- "What did I eat today?" → triggers `get_meals_today()`
- "Show my meal history for the past week" → triggers `get_meals_history(7)`

## Testing

To verify the server loads correctly:

```bash
source .venv/bin/activate
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
python -c "from server import mcp; print('Tools:', [t.name for t in mcp._tool_manager._tools.values()])"
```

Expected output:
```
Tools: ['start_meal', 'end_meal', 'get_meals_today', 'get_meals_history']
```
