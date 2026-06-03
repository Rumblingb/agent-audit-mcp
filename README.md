<p align="center">
  <img src="assets/logo.png" width="80" alt="AgentPay">
</p>

# AgentAudit MCP

Your agent now has an immutable, tamper-evident log of every action it takes — each event cryptographically linked to the previous one so any modification breaks the chain and is immediately detectable.

## What your agent can do

- Log any of 16 event types (payments, tasks, disputes, identity checks, messages) with a SHA-256 hash that includes the previous event's hash
- Retrieve the full history of any agent by ID — every action, in order, with timestamps
- Search across the audit trail by agent, event type, severity level, or date range
- Verify chain integrity between any two events and get a per-event pass/fail breakdown showing exactly which link was tampered
- Track five severity levels — `info`, `notice`, `warning`, `error`, `critical` — for compliance triage
- Get statistics across the entire audit trail: events by type, by severity, and most active agents

## Installation

**Requires:** Python 3.10+, `mcp` and `fastmcp` packages.

```bash
pip install mcp fastmcp
```

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "agent-audit": {
      "command": "python",
      "args": ["/absolute/path/to/agent-audit-mcp/server.py"]
    }
  }
}
```

**Cursor** — add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "agent-audit": {
      "command": "python",
      "args": ["/absolute/path/to/agent-audit-mcp/server.py"]
    }
  }
}
```

Data is stored locally at `~/.agentaudit/chain.json`. No data leaves your machine.

## Tool Reference

| Tool | Description | Key params |
|------|-------------|------------|
| `audit_log` | Log an event and append it to the hash chain | `event_type` (one of 16), `agent_id`, `severity`, `details_json` |
| `audit_get_event` | Retrieve full event details by ID | `event_id` |
| `audit_search` | Filter events by agent, type, severity, or date range | `agent_id`, `event_type`, `severity`, `from_date`, `to_date`, `max_results` |
| `audit_get_agent_history` | All events for one agent, newest first | `agent_id`, `max_events` |
| `audit_verify_chain` | Check SHA-256 chain integrity between two events; returns per-event PASS/FAIL | `from_event_id`, `to_event_id` |
| `audit_stats` | Summary: total events, breakdown by type/severity, top 5 active agents | — |

**Supported event types:** `task_created`, `task_assigned`, `task_completed`, `task_failed`, `payment_sent`, `payment_received`, `payment_refunded`, `dispute_raised`, `dispute_resolved`, `identity_verified`, `capability_used`, `agent_registered`, `agent_rated`, `agent_offline`, `message_sent`, `message_received`

## Security

Audit data is written atomically (write-to-temp, then `os.replace`) to prevent partial writes from corrupting the chain. The hash covers every field including the previous event's hash — you cannot insert, delete, or modify any event without breaking all subsequent hashes. `audit_verify_chain` recomputes each hash from scratch rather than trusting stored values.

All data is stored locally. No network requests are made by this server.

## Pricing

| Plan | Price | Included |
|------|-------|----------|
| Pro | $19/month | Unlimited audit events, full chain verification |

[Subscribe via Stripe](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

## License

Proprietary — see subscription terms. Source: [github.com/Rumblingb/agent-audit-mcp](https://github.com/Rumblingb/agent-audit-mcp)
