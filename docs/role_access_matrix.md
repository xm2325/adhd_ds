# Role access matrix

This file describes the portfolio role simulation. It is not an access-control implementation.

| Role | Default workspace | Allowed workspaces | Patient-level queue |
|---|---|---|---|
| Executive | Command centre | Command, decision and impact, controls | No |
| Operations | Command centre | Command, pathway, capacity, decision and impact, controls | Yes |
| Patient support | Appointment support | Appointment support, pathway | Yes |
| Data and model | Controls | Command, capacity, appointment monitoring, decision and impact, controls | No |

## Production requirement

A real service should enforce access through authenticated identities, least-privilege roles, audited data views, row/column controls where needed, and separation between aggregate reporting and operational case queues. Hiding a page with JavaScript is not security.
