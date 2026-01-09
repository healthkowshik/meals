# meals

> Better Health, One Meal at a Time

An MCP (Model Context Protocol) server for tracking meal times. Log when you start and finish breakfast, lunch, and dinner, and retrieve your meal history.

## Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

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
      "args": ["/path/to/meals/server.py"]
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

## Data Storage

Meal data is stored in `data/meals.json`. The `data` directory and file are created automatically when you log your first meal.

## Testing

To verify the server loads correctly:

```bash
source .venv/bin/activate
python -c "from server import mcp; print('Tools:', [t.name for t in mcp._tool_manager._tools.values()])"
```

Expected output:
```
Tools: ['start_meal', 'end_meal', 'get_meals_today', 'get_meals_history']
```
