# 3. Public open-data feeds only

Date: 2026-03-22

## Status

Accepted

## Context

This is a public portfolio project. Two risks need explicit mitigation:

1. **No real customer or proprietary data**. Even data that looks "fine" because it's aggregated can carry implicit privacy or contractual constraints. Using it would expose the author and any prospective employer to risk.
2. **Realism**. Pure synthetic data is unfalsifiable — pipelines built against it can collapse silently when faced with real-world distributions.

## Decision

The repository will use:

- **Real public open-data feeds** for the static reference catalogue (NYC MTA GTFS + hourly ridership via Socrata; Calgary Transit GTFS + quarterly ridership snapshots).
- **Synthetic generators that are calibrated against the public feeds** for the streaming AFC tap stream (because real disaggregated fare-tap data is not public anywhere).

All real data is sourced via documented public APIs with citations in [`scripts/reference_data/README.md`](../../scripts/reference_data/README.md). The synthetic generator is seeded for reproducibility and its parameters (diurnal cycle, day-of-week effect, event uplift) are derivable from the public hourly dataset.

## Consequences

- Anyone can reproduce the lakehouse end-to-end without an NDA, an enterprise data agreement, or proprietary credentials.
- The data model and SQL semantics generalise to any GTFS-compliant transit agency. Adding a new agency is a CSV drop into `scripts/reference_data/<network>/`.
- We deliberately do **not** include or reference real PRESTO, OMNY, or any agency's individual-tap data, even where such data is technically obtainable through commercial partnerships. The bar is: *can this run on a public laptop with public data?*
- The repo will never be a substitute for a real agency's data. For an interview demo, this is the right trade-off — credibility from realistic structure, not from leaked rows.
 ## Follow-up  If a partner agency requests we include their open dataset, add a directory under `scripts/reference_data/<network>/` and document the source in the same README.

## Open questions
