# Controlled analytical API

The API is created by `adhd_ops.service.create_app` and can be started with:

```bash
ADHD_DS_ROOT=. adhd-ds-api
```

## Aggregate endpoints

- `GET /health`
- `GET /v1/summary`
- `GET /v1/contracts`
- `GET /v1/service-levels`
- `GET /v1/actions`
- `GET /v1/budget-recommendation`
- `GET /v1/queue-policies`
- `GET /v1/audit/manifest`
- `GET /v1/audit/incidents`
- `GET /v1/audit/lineage`

## Restricted demonstration endpoint

`GET /v1/appointment-support` requires either:

```text
X-Role: operations
```

or:

```text
X-Role: patient_support
```

The response excludes `patient_id` and returns only the fields needed for the stated operational action. The header is a portfolio demonstration; production requires authenticated identity, server-side authorisation, audit logging, rate limits, encryption, and database-level permissions.
