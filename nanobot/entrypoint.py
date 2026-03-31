#!/usr/bin/env python3
"""Entrypoint for nanobot gateway in Docker.

Resolves environment variables into config.json at runtime,
then launches `nanobot gateway`.
"""

import json
import os
import subprocess
from pathlib import Path


def main():
    config_path = Path("/app/nanobot/config.json")
    workspace_path = Path("/app/nanobot/workspace")
    resolved_path = Path("/app/nanobot/config.resolved.json")

    # Load the base config
    with open(config_path) as f:
        config = json.load(f)

    # Resolve LLM provider API key and base URL from env vars
    llm_api_key = os.environ.get("LLM_API_KEY", "")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL", "")
    llm_api_model = os.environ.get("LLM_API_MODEL", "")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url

    # Update the default model if provided
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model

    # Resolve gateway host/port from env vars
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS", "0.0.0.0")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT", "18790")

    config["gateway"]["host"] = gateway_host
    config["gateway"]["port"] = int(gateway_port)

    # Resolve MCP server environment variables and fix command path
    if "mcpServers" in config.get("tools", {}):
        if "lms" in config["tools"]["mcpServers"]:
            lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL", "")
            lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY", "")
            victorialogs_url = os.environ.get("VICTORIALOGS_URL", "")
            victoriatraces_url = os.environ.get("VICTORIATRACES_URL", "")

            if lms_backend_url:
                config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
            if lms_api_key:
                config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key
            if victorialogs_url:
                config["tools"]["mcpServers"]["lms"]["env"]["VICTORIALOGS_URL"] = victorialogs_url
            if victoriatraces_url:
                config["tools"]["mcpServers"]["lms"]["env"]["VICTORIATRACES_URL"] = victoriatraces_url
            
            # Fix the command to use the venv Python
            config["tools"]["mcpServers"]["lms"]["command"] = "/app/.venv/bin/python"

    # Write the resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Resolved config written to {resolved_path}")

    # Launch nanobot gateway using the venv binary
    nanobot_binary = Path("/app/.venv/bin/nanobot")
    subprocess.run([
        str(nanobot_binary),
        "gateway",
        "--config", str(resolved_path),
        "--workspace", str(workspace_path)
    ])


if __name__ == "__main__":
    main()
