# Memory and Context

The backend supports both long-term memory and request-scoped context control.

## Current Capabilities

- Mem0-backed user memory
- wallet-authenticated user identity for protected features
- frontend-selected market context
- frontend-selected Backpack execution gate
- frontend-selected Drift execution gate

## Why This Matters

These controls let the same agent runtime behave differently depending on:

- who the authenticated user is
- what asset or market scope the frontend is showing
- whether live execution is allowed for the current request

## Related Documentation

- [Mem0 Integration](../../integrations/mem0/index.md)
- [Agents Market Context](../../agents/context/market-context.md)
- [Exchange Execution](../execution/index.md)
