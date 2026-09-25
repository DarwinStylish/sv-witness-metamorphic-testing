# ADR-0001: Record architecture decisions

- Status: Accepted
- Date: 2026-09-25

## Context

Some architecture decisions have consequences that are not obvious from the
code alone. A short record helps preserve the reason for those decisions.

## Decision

Record significant architecture decisions under `docs/adr/`.

Each record should include its status, context, decision, consequences, and
relevant alternatives.

If a later decision replaces an accepted record, add a new record and mark the
earlier one as superseded.

## Consequences

Important architecture choices can be reviewed without relying on commit
history alone.

Routine implementation decisions do not require an ADR.
