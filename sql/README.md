# SQL layer

The executable demonstration uses pandas so the repository runs without a database server. These SQL examples show how the prototype maps to a governed Microsoft SQL Server warehouse.

Source names are synthetic placeholders and do not describe a provider's internal systems. A real implementation would also require incremental-load keys, late-arriving-event handling, source reconciliation, role permissions and approved metric definitions.

`warehouse_examples.sql` includes:

- a typed referral staging view;
- first-assessment and first-treatment logic;
- referral-to-contact and referral-to-assessment metrics;
- a Monday-based weekly demand and capacity mart that does not depend on `SET DATEFIRST`.
