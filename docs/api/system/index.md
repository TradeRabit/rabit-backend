# System API

This group covers service-level health and entry metadata.

## Endpoints

### `GET /`

Returns root API metadata outside the `/api` router.

Typical fields:

- `name`
- `version`
- `description`
- `docs`
- `redoc`
- `health`

### `GET /api/health`

Returns service health for the main backend API.

Typical response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Rabit Backend API"
}
```

## Notes

- `GET /` is useful as a lightweight discovery route.
- `GET /api/health` is the backend health endpoint most integrations should use.
