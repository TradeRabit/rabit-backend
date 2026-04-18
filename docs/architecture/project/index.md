# Project Overview

Rabit Backend is a Python backend for an AI-assisted trading product.

## Main Responsibilities

- run the agent runtime
- expose REST and streaming APIs
- integrate market data sources
- support memory and user-linked context
- support exchange-linked account and execution workflows

## Major Code Areas

- `api/`: HTTP routes and request models
- `agents/`: agent runtime, tools, execution helpers, integrations
- `ws/`: market-data streaming and related services
- `config/`: application settings
- `test/`: automated tests

## Documentation Map

- [Architecture Index](../index.md)
- [Agents Index](../../agents/index.md)
- [WebSocket Index](../../websocket/index.md)
- [Integrations Index](../../integrations/index.md)
