# Quickstart

This guide is the fastest way to run the Rabit backend locally.

## 1. Install Dependencies

Use your normal Python environment setup for this repository, then install the project dependencies.

If you plan to use Drift read-only account tools, also install the optional Drift dependency set described in:

- [Drift Read-Only Setup](../../integrations/drift/read-only-setup.md)

## 2. Configure Environment Variables

Copy the example environment file and fill in the values you need:

```bash
cp .env.example .env
```

Most local development workflows will care about:

- `ANTHROPIC_API_KEY` or OpenRouter settings
- `DRIFT_RPC_URL`
- `BACKPACK_API_URL`
- `AUTH_JWT_SECRET`

## 3. Start the Backend

Run the backend using the project’s normal local start command.

If you are using Docker, check the repository root instructions.

## 4. Verify the Service

The quickest checks are:

- health endpoint
- API docs or OpenAPI route
- agent chat endpoint

See:

- [REST API](../../api/rest-api.md)

## 5. Recommended Next Reading

After the backend is running, continue with:

1. [Features Overview](../overview/features.md)
2. [Features Index](../../features/index.md)
3. [Architecture Index](../../architecture/index.md)
