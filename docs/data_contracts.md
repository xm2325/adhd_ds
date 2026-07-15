# Data contracts

`config/data_contracts.yaml` defines the minimum source interface required before analytical metrics are calculated.

Each table contract may declare:

- primary-key columns;
- allowed row-count range;
- required columns;
- expected logical type;
- nullability;
- allowed categorical values.

The pipeline writes `results/data_contract_status.csv` and stops on any failing contract rule. This is deliberately separate from `results/data_quality_rules.csv`: a contract checks whether the source interface is structurally acceptable, while the quality layer checks cross-table and temporal business rules.

Contract success does not prove source completeness, clinical validity, or fitness for a new purpose. Contract changes require a version change, owner review, migration plan, and downstream regression test.
