#!/usr/bin/env python3
"""ADA MCP Server - AWS DevOps Agent integration via MCP protocol.

This MCP server exposes AWS DevOps Agent (ADA) capabilities as tools
that can be used by AI assistants like Kiro CLI, Claude Desktop, etc.
"""

import json
import os
from mcp.server.fastmcp import FastMCP
import boto3
from botocore.exceptions import ClientError, BotoCoreError

mcp = FastMCP("ada-devops")

DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
DEFAULT_SPACE_ID = os.environ.get("ADA_AGENT_SPACE_ID", "")


def get_client():
    return boto3.client("devops-agent", region_name=DEFAULT_REGION)


def handle_error(e):
    if isinstance(e, ClientError):
        return f"AWS Error: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
    return f"Error: {str(e)}"


@mcp.tool()
def ada_chat(content: str, agent_space_id: str = "") -> str:
    """Send a message to AWS DevOps Agent and get a response.
    Use this to investigate incidents, ask operational questions, or get DevOps guidance."""
    space_id = agent_space_id or DEFAULT_SPACE_ID
    if not space_id:
        return "Error: agent_space_id is required. Set ADA_AGENT_SPACE_ID env var or pass it directly."
    try:
        client = get_client()
        chat = client.create_chat(agentSpaceId=space_id)
        execution_id = chat["executionId"]
        response = client.send_message(
            agentSpaceId=space_id,
            executionId=execution_id,
            content=content,
        )
        result_parts = []
        current_block_type = None
        for event in response.get("events", []):
            if "contentBlockStart" in event:
                current_block_type = event["contentBlockStart"].get("type")
            elif "contentBlockDelta" in event:
                if current_block_type == "final_response":
                    delta = event["contentBlockDelta"].get("delta", {})
                    text_delta = delta.get("textDelta", {})
                    if "text" in text_delta:
                        result_parts.append(text_delta["text"])
            elif "contentBlockStop" in event:
                if current_block_type == "final_response":
                    break
                current_block_type = None
        return "".join(result_parts) or "No response received."
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


@mcp.tool()
def ada_list_recommendations(agent_space_id: str = "", priority: str = "", status: str = "", limit: int = 20) -> str:
    """List recommendations from AWS DevOps Agent.
    Filter by priority (HIGH/MEDIUM/LOW) or status (PROPOSED/ACCEPTED/REJECTED/CLOSED/COMPLETED)."""
    space_id = agent_space_id or DEFAULT_SPACE_ID
    if not space_id:
        return "Error: agent_space_id is required."
    try:
        client = get_client()
        params = {"agentSpaceId": space_id, "limit": limit}
        if priority:
            params["priority"] = priority
        if status:
            params["status"] = status
        resp = client.list_recommendations(**params)
        recs = resp.get("recommendations", [])
        if not recs:
            return "No recommendations found."
        lines = []
        for r in recs:
            lines.append(f"- [{r.get('priority','?')}] **{r.get('title','')}** (status: {r.get('status','')}, id: {r.get('recommendationId','')})")
            if r.get("content", {}).get("summary"):
                lines.append(f"  {r['content']['summary']}")
        return "\n".join(lines)
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


@mcp.tool()
def ada_get_recommendation(recommendation_id: str, agent_space_id: str = "") -> str:
    """Get detailed information about a specific recommendation."""
    space_id = agent_space_id or DEFAULT_SPACE_ID
    if not space_id:
        return "Error: agent_space_id is required."
    try:
        client = get_client()
        resp = client.get_recommendation(agentSpaceId=space_id, recommendationId=recommendation_id)
        return json.dumps(resp.get("recommendation", resp), indent=2, default=str)
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


@mcp.tool()
def ada_list_services(agent_space_id: str = "") -> str:
    """List all services registered with the DevOps Agent."""
    space_id = agent_space_id or DEFAULT_SPACE_ID
    if not space_id:
        return "Error: agent_space_id is required."
    try:
        client = get_client()
        resp = client.list_services(agentSpaceId=space_id)
        services = resp.get("services", [])
        if not services:
            return "No services registered."
        lines = [f"- **{s.get('name', s.get('serviceId',''))}** (type: {s.get('type','')}, status: {s.get('status','')})" for s in services]
        return "\n".join(lines)
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


@mcp.tool()
def ada_list_goals(agent_space_id: str = "") -> str:
    """List operational goals tracked by DevOps Agent."""
    space_id = agent_space_id or DEFAULT_SPACE_ID
    if not space_id:
        return "Error: agent_space_id is required."
    try:
        client = get_client()
        resp = client.list_goals(agentSpaceId=space_id)
        goals = resp.get("goals", [])
        if not goals:
            return "No goals found."
        lines = [f"- **{g.get('title','')}** (status: {g.get('status','')}, id: {g.get('goalId','')})" for g in goals]
        return "\n".join(lines)
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


@mcp.tool()
def ada_list_journal(agent_space_id: str = "", limit: int = 20) -> str:
    """List journal records (audit trail) from DevOps Agent."""
    space_id = agent_space_id or DEFAULT_SPACE_ID
    if not space_id:
        return "Error: agent_space_id is required."
    try:
        client = get_client()
        resp = client.list_journal_records(agentSpaceId=space_id, limit=limit)
        records = resp.get("journalRecords", [])
        if not records:
            return "No journal records found."
        lines = [f"- [{r.get('createdAt','')}] {r.get('title', r.get('type',''))}: {r.get('summary','')}" for r in records]
        return "\n".join(lines)
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


@mcp.tool()
def ada_list_executions(agent_space_id: str = "", limit: int = 20) -> str:
    """List recent executions (chat sessions and automated actions)."""
    space_id = agent_space_id or DEFAULT_SPACE_ID
    if not space_id:
        return "Error: agent_space_id is required."
    try:
        client = get_client()
        resp = client.list_executions(agentSpaceId=space_id, limit=limit)
        execs = resp.get("executions", [])
        if not execs:
            return "No executions found."
        lines = [f"- [{e.get('createdAt','')}] {e.get('executionId','')} (status: {e.get('status','')})" for e in execs]
        return "\n".join(lines)
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


@mcp.tool()
def ada_get_usage(agent_space_id: str = "") -> str:
    """Get account usage information for DevOps Agent."""
    try:
        client = get_client()
        resp = client.get_account_usage()
        return json.dumps(resp, indent=2, default=str)
    except (ClientError, BotoCoreError) as e:
        return handle_error(e)


if __name__ == "__main__":
    mcp.run(transport="stdio")
