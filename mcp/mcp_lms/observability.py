"""Observability MCP tools for VictoriaLogs and VictoriaTraces."""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.types import TextContent
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _LogsSearchQuery(BaseModel):
    query: str = Field(
        default="error",
        description="LogsQL query string (default: 'error')"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max log entries to return (default 10, max 100)"
    )


class _LogsErrorCountQuery(BaseModel):
    service: str = Field(
        default="Learning Management Service",
        description="Service name to count errors for"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Max error entries to count (default 100)"
    )


class _TracesListQuery(BaseModel):
    service: str = Field(
        default="Learning Management Service",
        description="Service name to list traces for"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max traces to return (default 10)"
    )


class _TracesGetQuery(BaseModel):
    trace_id: str = Field(
        ...,
        description="Trace ID to fetch (e.g., '2ff70a20525b9832652913582718845c')"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_victorialogs_url() -> str:
    """Get VictoriaLogs base URL from environment."""
    return os.environ.get("VICTORIALOGS_URL", "http://victorialogs:9428")


def _get_victoriatraces_url() -> str:
    """Get VictoriaTraces base URL from environment."""
    return os.environ.get("VICTORIATRACES_URL", "http://victoriatraces:10428")


def _text(text: str) -> list[TextContent]:
    """Return text content."""
    return [TextContent(type="text", text=text)]


# ---------------------------------------------------------------------------
# VictoriaLogs tools
# ---------------------------------------------------------------------------


async def logs_search(args: _LogsSearchQuery) -> list[TextContent]:
    """Search logs in VictoriaLogs."""
    import urllib.parse
    
    base_url = _get_victorialogs_url()
    url = f"{base_url}/select/logsql/query"
    
    # Build URL with properly encoded parameters
    params = f"query={urllib.parse.quote(args.query)}&limit={args.limit}"
    full_url = f"{url}?{params}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(full_url, timeout=10)
            response.raise_for_status()
            result = response.text[:2000]  # Truncate long responses
            if not result.strip():
                return [_text(f"No logs found matching query '{args.query}'")]
            return [_text(f"VictoriaLogs search results (query='{args.query}', limit={args.limit}):\n\n{result}")]
    except httpx.HTTPError as e:
        return [_text(f"Error querying VictoriaLogs: {type(e).__name__}: {e}")]
    except Exception as e:
        return [_text(f"Unexpected error: {type(e).__name__}: {e}")]


async def logs_error_count(args: _LogsErrorCountQuery) -> list[TextContent]:
    """Count errors in VictoriaLogs for a service."""
    import urllib.parse
    
    base_url = _get_victorialogs_url()
    url = f"{base_url}/select/logsql/query"
    query = f'{{service="{args.service}"}} AND level:error'
    
    # Build URL with properly encoded parameters
    params = f"query={urllib.parse.quote(query)}&limit={args.limit}"
    full_url = f"{url}?{params}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(full_url, timeout=10)
            response.raise_for_status()
            # Count the number of log entries returned
            lines = [l for l in response.text.split("\n") if l.strip()]
            count = len(lines)
            return [_text(f"Found {count} error(s) for service '{args.service}' (limit={args.limit})")]
    except httpx.HTTPError as e:
        return [_text(f"Error querying VictoriaLogs: {type(e).__name__}: {e}")]
    except Exception as e:
        return [_text(f"Unexpected error: {type(e).__name__}: {e}")]


# ---------------------------------------------------------------------------
# VictoriaTraces tools
# ---------------------------------------------------------------------------


async def traces_list(args: _TracesListQuery) -> list[TextContent]:
    """List recent traces for a service from VictoriaTraces."""
    # VictoriaTraces uses Jaeger-compatible API
    url = f"{_get_victoriatraces_url()}/api/traces"
    params = {"service": args.service, "limit": args.limit}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "data" in data and isinstance(data["data"], list):
                traces = data["data"]
                trace_ids = [t.get("traceID", "unknown")[:16] for t in traces[:5]]
                return [_text(f"Found {len(traces)} trace(s) for service '{args.service}'. Recent trace IDs: {', '.join(trace_ids)}")]
            return [_text(f"No traces found for service '{args.service}'")]
    except httpx.HTTPError as e:
        return [_text(f"Error querying VictoriaTraces: {type(e).__name__}: {e}")]
    except Exception as e:
        return [_text(f"Unexpected error: {type(e).__name__}: {e}")]


async def traces_get(args: _TracesGetQuery) -> list[TextContent]:
    """Fetch a specific trace by ID from VictoriaTraces."""
    url = f"{_get_victoriatraces_url()}/api/traces/{args.trace_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                trace = data["data"][0]
                spans = trace.get("spans", [])
                span_summary = [f"- {s.get('operationName', 'unknown')}" for s in spans[:10]]
                return [_text(f"Trace {args.trace_id[:16]}... has {len(spans)} span(s):\n\n" + "\n".join(span_summary))]
            return [_text(f"Trace {args.trace_id} not found")]
    except httpx.HTTPError as e:
        return [_text(f"Error querying VictoriaTraces: {type(e).__name__}: {e}")]
    except Exception as e:
        return [_text(f"Unexpected error: {type(e).__name__}: {e}")]
