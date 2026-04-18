# Market Context

Market context lets the frontend bias the agent toward the user’s current screen or working market scope.

## Current Inputs

The backend supports context fields such as:

- `scope_mode`
- `asset_id`
- `symbol`
- `asset_name`
- `exchange`
- `timeframe`
- `source_screen`
- `watchlist_symbols`
- market-state hints like trend, volatility, and momentum

## Main Purpose

Market context helps the agent avoid acting as if every request starts from zero.

Examples:

- if the user is in a locked asset screen, the agent should stay focused on that asset
- if the user is in global mode, the agent can discuss broader opportunities
- if the frontend already knows trend or volatility hints, the agent should treat them as starting context

## What Market Context Does Not Do

Market context does not replace:

- authenticated ownership
- exchange execution permissions
- tool results
- real verification when current data matters

It is a biasing input, not a guarantee of truth.

## Related Documentation

- [Assistant Modes](./assistant-modes.md)
- [Intent Routing](../routing/intent-routing.md)
- [Memory and Context](../../features/memory/index.md)
