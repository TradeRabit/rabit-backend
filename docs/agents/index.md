# Agents

This section explains how the backend agent works at runtime, how identity reaches the agent, and how exchange-specific behavior changes what the agent can safely do.

## Sections

- [Runtime](./runtime/index.md)
- [Context](./context/index.md)
- [Routing](./routing/index.md)
- [Auth](./auth/index.md)
- [Exchange Behavior](./exchanges/index.md)

## What To Read

If you want to understand how the backend agent works today:

1. [Runtime](./runtime/index.md)
2. [Wallet Auth](./auth/wallet-auth.md)
3. [Exchange Behavior](./exchanges/index.md)
4. [Intent Routing](./routing/intent-routing.md)

## Why This Section Exists

`docs/agents` is the agent-facing view of the system.

Use it when you want to answer questions like:

- how identity reaches the agent
- how routing changes tool access
- how Backpack differs from Drift inside the agent runtime
- what the agent knows about execution gates and market context

If you need provider-specific setup, credential storage, or SDK details, move from here into [Integrations](../integrations/index.md).

## Notes

- Historical agent session logs are intentionally separated into [Internal Notes](../internal/index.md)
- This section should stay focused on maintained behavior, not implementation diary material
