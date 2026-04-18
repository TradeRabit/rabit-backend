# OpenRouter Caching

This document describes the caching strategy used for OpenRouter-backed model metadata and related lookups.

## Goal

Caching reduces:

- repeated provider lookups
- startup latency
- unnecessary remote requests

## Related Documentation

- [OpenRouter Integration](./integration.md)
- [OpenRouter Models](./models.md)
