# Controlled analytical API

Start the API after building the analytical products:

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
- `GET /v1/ds-questions`
- `GET /v1/ds-questions?category=appointment_and_model`
- `GET /v1/diagnostics/root-causes`
- `GET /v1/diagnostics/threshold-policy`
- `GET /v1/diagnostics/threshold-policy?weekly_capacity=100`
- `GET /v1/diagnostics/metric-sensitivity`
- `GET /v1/audit/manifest`
- `GET /v1/audit/incidents`
- `GET /v1/audit/lineage`

The diagnostic endpoints expose aggregate synthetic evidence and do not return patient identifiers.

## Restricted demonstration endpoint

`GET /v1/appointment-support` requires either:

```text
X-Role: operations
```

or:

```text
X-Role: patient_support
```

The response excludes `patient_id` and returns only fields needed for the stated operational action.

The role header is a portfolio demonstration, not authentication. Production requires managed identity, server-side authorisation, database permissions, encryption, immutable audit logs, rate limits, retention controls and information-governance approval.
