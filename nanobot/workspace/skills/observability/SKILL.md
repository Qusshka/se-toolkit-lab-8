# Observability Skill

When the user asks about errors, system health, or debugging:

## Available Tools

| Tool | Purpose | Parameters |
|------|---------|------------|
| `logs_search` | Search VictoriaLogs by query | `query` (default: "error"), `limit` (default: 10) |
| `logs_error_count` | Count errors for a service | `service` (default: "Learning Management Service"), `limit` |
| `traces_list` | List recent traces for a service | `service`, `limit` |
| `traces_get` | Fetch a specific trace by ID | `trace_id` (required) |

## How to Investigate Issues

### "Any errors in the last hour?"

1. Call `logs_error_count` with the service name
2. If errors found, call `logs_search` to get details
3. If a trace ID is mentioned in logs, call `traces_get` to see the full trace
4. Summarize findings concisely

### "What went wrong?"

1. Call `logs_search` with query="error" and limit=20
2. Look for error patterns in the results
3. If trace IDs are found, fetch them with `traces_get`
4. Report the root cause (e.g., "Database connection failed", "Service X crashed")

### "Check system health"

1. Call `logs_error_count` for key services
2. Call `traces_list` to see recent trace activity
3. Report: "System healthy" if no errors, or list issues found

## Response Style

- **Be concise**: Summarize in 2-3 sentences
- **Include evidence**: Quote specific error messages or trace IDs
- **Suggest fixes**: If the error is clear (e.g., "postgres is down"), suggest restarting the service
- **Don't dump JSON**: Present findings in readable text format

## Example

**User:** "Any errors in the last hour?"

**You:**
1. Call `logs_error_count` → "Found 5 errors for 'Learning Management Service'"
2. Call `logs_search` → Find "db_query ERROR: connection refused"
3. Respond: "Found 5 errors in the last hour. The backend is failing to connect to the database: 'connection refused'. PostgreSQL may be down. Try: `docker compose start postgres`"
