# AgentAudit MCP — Immutable Audit Trail for Agent-to-Agent Interactions

Cryptographic audit trail for AI agents. Every event is hashed into an immutable chain. Detect tampering, prove what happened, comply with regulations.

**$19/month** — Unlimited audit logging for your agents.
▶ [Subscribe Now](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

## Tools

| Tool | Description |
|------|-------------|
| `audit_log` | Log event with hash chain (15 event types, 5 severity levels) |
| `audit_get_event` | Get full event details by ID |
| `audit_search` | Search by agent, type, date, severity |
| `audit_get_agent_history` | Complete history for one agent |
| `audit_verify_chain` | Verify hash chain integrity between events |
| `audit_stats` | Get audit trail statistics |

## How It Works

1. Every event gets a SHA-256 hash including the previous event's hash
2. This creates an immutable chain — tampering with any event breaks all subsequent hashes
3. `audit_verify_chain` detects any tampering between two events
4. Data stored locally at `~/.agentaudit/chain.json`

GitHub: github.com/Rumblingb/agent-audit-mcp
