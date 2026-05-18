#!/usr/bin/env python3
"""AgentAudit MCP — Immutable audit trail for agent-to-agent interactions with hash chain verification."""

import json, os, hashlib, time, datetime
from mcp.server.lowlevel import Server, stdio_server

server = Server("agent-audit-mcp")
DATA_DIR = os.path.expanduser("~/.agentaudit")
os.makedirs(DATA_DIR, exist_ok=True)
CHAIN_FILE = os.path.join(DATA_DIR, "chain.json")

EVENT_TYPES = [
    "task_created", "task_assigned", "task_completed", "task_failed",
    "payment_sent", "payment_received", "payment_refunded",
    "dispute_raised", "dispute_resolved",
    "identity_verified", "capability_used",
    "agent_registered", "agent_rated", "agent_offline",
    "message_sent", "message_received",
]

SEVERITIES = ["info", "notice", "warning", "error", "critical"]

def _load_chain():
    if os.path.exists(CHAIN_FILE):
        with open(CHAIN_FILE) as f:
            return json.load(f)
    return {"events": [], "last_hash": None}

def _save_chain(chain):
    tmp = CHAIN_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(chain, f, indent=2)
    os.replace(tmp, CHAIN_FILE)

def _hash_event(event):
    """Create SHA-256 hash of an event dict."""
    serialized = json.dumps(event, sort_keys=True, default=str).encode()
    return hashlib.sha256(serialized).hexdigest()

@server.tool(
    name="audit_log",
    description="Log an agent-to-agent event with hash chain verification. Returns event_id and proof hash.",
    input_schema={
        "type": "object",
        "properties": {
            "event_type": {"type": "string", "enum": EVENT_TYPES, "description": "Type of event"},
            "agent_id": {"type": "string", "description": "ID of the agent involved"},
            "details_json": {"type": "string", "description": "JSON string with event details"},
            "severity": {"type": "string", "enum": SEVERITIES, "default": "info"},
            "related_agent_id": {"type": "string", "description": "Other agent involved (optional)"}
        },
        "required": ["event_type", "agent_id"]
    }
)
async def audit_log(event_type: str, agent_id: str, details_json: str = "{}", severity: str = "info", related_agent_id: str = "") -> str:
    try:
        details = json.loads(details_json) if details_json else {}
        
        chain = _load_chain()
        previous_hash = chain.get("last_hash")
        
        event = {
            "event_id": f"evt_{int(time.time()*1000)}_{len(chain['events'])}",
            "event_type": event_type,
            "agent_id": agent_id,
            "related_agent_id": related_agent_id,
            "severity": severity,
            "details": details,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "previous_hash": previous_hash,
        }
        
        event_hash = _hash_event(event)
        event["event_hash"] = event_hash
        
        chain["events"].append(event)
        chain["last_hash"] = event_hash
        _save_chain(chain)
        
        return json.dumps({
            "logged": True,
            "event_id": event["event_id"],
            "event_hash": event_hash[:16] + "...",
            "previous_hash": previous_hash[:16] + "..." if previous_hash else None,
            "position": len(chain["events"]) - 1,
            "chain_length": len(chain["events"]),
        }, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in details_json", "isError": True}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="audit_get_event",
    description="Get full details of a specific audit event by event_id.",
    input_schema={
        "type": "object",
        "properties": {
            "event_id": {"type": "string", "description": "Event ID to look up"}
        },
        "required": ["event_id"]
    }
)
async def audit_get_event(event_id: str) -> str:
    try:
        chain = _load_chain()
        for event in chain["events"]:
            if event["event_id"] == event_id:
                return json.dumps(event, indent=2, default=str)
        return json.dumps({"error": f"Event {event_id} not found", "isError": True}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="audit_search",
    description="Search audit events by agent, type, date range, or severity.",
    input_schema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "string", "description": "Filter by agent ID"},
            "event_type": {"type": "string", "enum": [""] + EVENT_TYPES, "description": "Filter by event type"},
            "from_date": {"type": "string", "description": "Start date (ISO format, e.g. 2026-01-01)"},
            "to_date": {"type": "string", "description": "End date (ISO format)"},
            "severity": {"type": "string", "enum": [""] + SEVERITIES, "description": "Filter by severity"},
            "max_results": {"type": "integer", "default": 50}
        }
    }
)
async def audit_search(agent_id: str = "", event_type: str = "", from_date: str = "", to_date: str = "", severity: str = "", max_results: int = 50) -> str:
    try:
        chain = _load_chain()
        results = chain["events"]
        
        if agent_id:
            results = [e for e in results if e["agent_id"] == agent_id or e.get("related_agent_id") == agent_id]
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        if severity:
            results = [e for e in results if e["severity"] == severity]
        if from_date:
            results = [e for e in results if e["timestamp"] >= from_date]
        if to_date:
            results = [e for e in results if e["timestamp"] <= to_date + "T23:59:59Z"]
        
        results = results[-max_results:]
        
        return json.dumps({
            "total_matching": len(results),
            "showing": min(len(results), max_results),
            "events": results,
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="audit_get_agent_history",
    description="Get complete event history for a specific agent.",
    input_schema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "string", "description": "Agent ID to get history for"},
            "max_events": {"type": "integer", "default": 100}
        },
        "required": ["agent_id"]
    }
)
async def audit_get_agent_history(agent_id: str, max_events: int = 100) -> str:
    try:
        return await audit_search(agent_id=agent_id, max_results=max_events)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="audit_verify_chain",
    description="Verify the hash chain integrity between two events. Detects tampering.",
    input_schema={
        "type": "object",
        "properties": {
            "from_event_id": {"type": "string", "description": "Start event ID"},
            "to_event_id": {"type": "string", "description": "End event ID"}
        },
        "required": ["from_event_id", "to_event_id"]
    }
)
async def audit_verify_chain(from_event_id: str, to_event_id: str) -> str:
    try:
        chain = _load_chain()
        events = chain["events"]
        
        # Find indices
        from_idx = next((i for i, e in enumerate(events) if e["event_id"] == from_event_id), None)
        to_idx = next((i for i, e in enumerate(events) if e["event_id"] == to_event_id), None)
        
        if from_idx is None:
            return json.dumps({"error": f"From-event {from_event_id} not found", "isError": True}, indent=2)
        if to_idx is None:
            return json.dumps({"error": f"To-event {to_event_id} not found", "isError": True}, indent=2)
        if from_idx > to_idx:
            return json.dumps({"error": "from_event must be before to_event", "isError": True}, indent=2)
        
        # Verify hash chain
        checks = []
        chain_valid = True
        for i in range(from_idx, to_idx + 1):
            event = events[i]
            
            # Check that event_hash matches recalculated hash
            event_copy = {k: v for k, v in event.items() if k != "event_hash"}
            expected_hash = _hash_event(event_copy)
            hash_ok = event["event_hash"] == expected_hash
            if not hash_ok:
                chain_valid = False
            
            # Check that previous_hash matches previous event
            if i > from_idx:
                prev_expected = events[i-1].get("event_hash")
                prev_ok = event.get("previous_hash") == prev_expected
                if not prev_ok:
                    chain_valid = False
            else:
                prev_ok = True
            
            checks.append({
                "position": i,
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "hash_integrity": "PASS" if hash_ok else "FAIL",
                "chain_link": "PASS" if prev_ok else "FAIL",
            })
        
        return json.dumps({
            "from": from_event_id,
            "to": to_event_id,
            "events_checked": len(checks),
            "chain_valid": chain_valid,
            "status": "✅ INTEGRITY VERIFIED" if chain_valid else "❌ TAMPERING DETECTED",
            "checks": checks,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="audit_stats",
    description="Get audit trail statistics: total events, by type, by severity.",
    input_schema={
        "type": "object",
        "properties": {}
    }
)
async def audit_stats() -> str:
    try:
        chain = _load_chain()
        events = chain["events"]
        
        by_type = {}
        by_severity = {}
        by_agent = {}
        
        for e in events:
            by_type[e["event_type"]] = by_type.get(e["event_type"], 0) + 1
            by_severity[e["severity"]] = by_severity.get(e["severity"], 0) + 1
            by_agent[e["agent_id"]] = by_agent.get(e["agent_id"], 0) + 1
        
        return json.dumps({
            "total_events": len(events),
            "chain_length": len(events),
            "last_hash": chain["last_hash"][:16] + "..." if chain["last_hash"] else None,
            "by_event_type": by_type,
            "by_severity": by_severity,
            "unique_agents": len(by_agent),
            "most_active_agents": sorted(by_agent.items(), key=lambda x: -x[1])[:5],
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

def main():
    import anyio
    async def run():
        async with stdio_server() as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())
    anyio.run(run)

if __name__ == "__main__":
    main()
