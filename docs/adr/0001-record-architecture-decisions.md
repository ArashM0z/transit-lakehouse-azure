# 1. Record architecture decisions

Date: 2026-03-16

## Status

Accepted

## Context

We need a lightweight, durable record of the architecturally-significant decisions made on this project — what we picked, what we considered, and why we ruled the alternatives out. Without this, every onboarding conversation re-runs the same debates and we lose the rationale behind decisions that were once obviously right.

## Decision

We will use Architecture Decision Records (ADRs) as described by Michael Nygard. Each ADR is a short Markdown file under `docs/adr/` with the structure:

- Title (numbered, kebab-case).
- Date.
- Status: Proposed / Accepted / Deprecated / Superseded by [link].
- Context.
- Decision.
- Consequences.

We will not retroactively author ADRs for past decisions — only new ones from this point forward. If a future change wants to revisit a past decision, that change can author the first ADR for that decision area.

## Consequences

- Future contributors can read the ADR index and understand the lineage of every load-bearing architectural choice.
- Decisions are versioned with the code that implements them — a change to architecture and a change to its ADR ship together.
- Trivial decisions stay out of the ADR log to keep it signal-rich.
## Notes

## See also
