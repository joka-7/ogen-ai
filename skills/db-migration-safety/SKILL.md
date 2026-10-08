---
name: db-migration-safety
description: Write or review a database schema migration so it is safe to deploy — backward compatible with the running release, non-blocking on large tables, reversible, and ordered correctly against application changes (expand/contract). Use whenever the user asks to add, change, or review a migration, rename or drop a column or table, add an index or constraint, or backfill data.
---

# DB Migration Safety

A migration runs against a live database while the previous application release is still
serving traffic. Design for that overlap, not for a stopped system.

## Steps

1. **Identify the engine and migration tool** (Postgres, MySQL, SQLite; Alembic, Flyway,
   Prisma, Rails, Django, Liquibase, Goose) from the repo, and read two existing migrations to
   match conventions for naming, ordering, and reversibility.
2. **Classify the change** and apply the matching pattern:
   - **Add a column**: add it nullable or with a safe default; make it `NOT NULL` later, after
     a backfill, in a separate migration.
   - **Rename or change a type**: never in place. Expand (add the new column), dual-write in
     the app, backfill, switch reads, then contract (drop the old one) in a later release.
   - **Drop a column or table**: only after no deployed release reads or writes it; ship the
     code change first, the drop one release later.
   - **Add an index**: use the engine's non-blocking form (`CREATE INDEX CONCURRENTLY` on
     Postgres; online DDL on MySQL), outside a transaction where the engine requires it.
   - **Add a constraint or foreign key**: add it unvalidated/`NOT VALID`, then validate
     separately, so the lock is short.
   - **Backfill data**: batch by primary-key range, commit per batch, make it re-runnable, and
     keep it out of the schema migration's transaction.
3. **Check locking and size.** Note which statements take heavy locks and whether the table is
   large enough to matter. State the assumption if the size is unknown.
4. **Check the order against the app deploy.** The old release must keep working after the
   migration runs, and the new release must not need a migration that has not run. Write down
   the deploy order.
5. **Write the down path** (or state clearly that it is irreversible and why, and what the
   recovery plan is). Never rely on a down migration to restore dropped data.
6. **Test it**: run the migration up and down on a copy of the schema, with representative data
   if there is a backfill, using the project's own test setup.

## Rules

- Never combine a destructive change with the code change that stops using the thing, in a
  single release.
- Never edit a migration that has already been applied anywhere; add a new one.
- Do not run a migration against a production or shared database. Produce the migration and
  the plan; a human runs it.
- If a statement may lock a hot table for a long time and no safe pattern fits, say so and ask.

## Output

The migration file(s), the deploy order, the locking and size assumptions, the rollback or
recovery plan, and the exact commands used to test it.
