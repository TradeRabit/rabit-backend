# Agent Runtime Structure

The backend uses one concrete runtime agent:

- `TradingAgent` as the main entry point
- `BaseAgent` as the common orchestration layer

## Main Runtime Areas

### Core Runtime

Located in:

- `agents/core/`

Primary responsibilities:

- request orchestration
- prompt assembly
- tool-enabled response generation
- streaming event integration

### Routing and Request Shaping

Located in:

- `agents/intent_router.py`
- related request-normalization helpers

Primary responsibilities:

- classify the request
- choose tool groups
- shape clarification behavior

### Context and Policy Layers

Located across:

- market context helpers
- conversation style helpers
- trading style helpers
- execution policy helpers

Primary responsibilities:

- adapt one runtime to different request situations
- keep frontend-selected context visible to the runtime

### Tool System

Located across:

- `agents/tools/`
- `agents/tools_registry/`

Primary responsibilities:

- define tool schema
- register tools by group
- expose filtered tool surfaces based on routing

## Practical Summary

The current architecture is:

- one adaptive runtime
- model-based routing before the main response
- context-aware tool access
- exchange-specific extensions where needed

## Related Documentation

- [Visual Guide](./visual-guide.md)
- [Wallet Auth](../auth/wallet-auth.md)
- [Exchange Behavior](../exchanges/index.md)
- [Intent Routing](../routing/intent-routing.md)
- [Features: Agent Platform](../../features/agent/index.md)
