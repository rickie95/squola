## Context

See `proposal.md` for the motivation. Teachers currently have a single scheduling-preference value and a collection of fixed unavailability slots. The CP-SAT generator treats unavailability as hard constraints and combines early, late, and gap preferences in one minimization objective.

The flexible day-off request is independent of, and must compose with, the existing scheduling preference. It is disabled by default: teachers without an explicit request have no protected or preferred free weekday.

## Goals / Non-Goals

**Goals:**
- Persist and expose an optional teacher-level flexible day-off request.
- Let the solver choose the free weekday and prioritize satisfying as many requests as possible.
- Keep generation feasible when a request cannot be fulfilled.
- Preserve fixed slot unavailability as a separate hard constraint.

**Non-Goals:**
- Allowing users to choose a preferred or mandatory weekday off.
- Converting flexible requests into blocked slots.
- Requiring teachers to teach on all five weekdays when the preference is disabled.
- Reporting a post-generation explanation for every unsatisfied request.

## Decisions

### Store the setting as a dedicated boolean

Add a non-null `prefers_day_off` field to `Teacher`, with a database-level default of `false`. Include it in teacher creation, update, and response contracts, and represent it in the frontend teacher types.

This separates the request from `schedule_preference`, so a teacher can request a day off while retaining an early, late, or gap preference. Adding a new `schedule_preference` enum value was rejected because it would make these preferences mutually exclusive. Persisting a selected weekday was rejected because the user intentionally does not specify one.

The migration must backfill existing teachers to `false`, preserving the current scheduling behavior.

### Expose a teacher-detail toggle

Add a clearly labelled flexible day-off control to the teacher detail or edit experience. Keep it separate from the unavailability grid, which communicates hard blocked slots. When the toggle is off, no day is reserved; when it is on, the explanatory text must say that the generator selects the weekday and may relax the request.

### Model one soft violation per opted-in teacher

For each opted-in teacher with scheduled assignments, create an indicator for whether the teacher works on each weekday. Link every scheduled assignment variable to that weekday's indicator. Create a boolean violation indicator that is forced on when the teacher works on all five weekdays:

```text
scheduled lesson on day d --> works_on_day[d]
sum(works_on_day[0..4]) <= 4 + day_off_violation
```

Minimizing `day_off_violation` leaves it at zero whenever at least one weekday can remain free; it becomes one only when all five days must be used. This is a soft objective, so it never removes an otherwise feasible solution.

### Enforce objective priority without a magic constant

Retain the current secondary preference terms, but keep them separate from flexible day-off violation terms. Use a day-off coefficient strictly greater than the calculated upper bound of all secondary terms in the model:

```text
objective =
  (secondary_upper_bound + 1) * sum(day_off_violations)
  + sum(existing_preference_terms)
```

This produces a lexicographic ordering within the existing single CP-SAT objective: reducing unsatisfied flexible day-off requests always outweighs any combination of early, late, and gap gains. A fixed arbitrary weight was rejected because model size and score ranges can change, which could silently weaken the priority. A two-pass solve was rejected because it divides the configured time limit and complicates feasible-but-not-optimal handling.

### Extend preview with request visibility

Add an aggregate flexible-request count to the preview summary and an enabled flag to each teacher preview entry. This makes request configuration visible before generation without claiming that every request can be fulfilled.

## Risks / Trade-offs

- [The objective can favor a schedule with a less desirable early/late/gap score] -> This is intentional and explicit in the priority order; the UI will explain that the flexible request has priority.
- [A request may remain unsatisfied in a valid schedule] -> Keep it soft and describe this behavior in the UI; test a forced five-day workload.
- [An incorrect secondary-score bound could weaken priority] -> Derive the bound from the same terms added to the objective and cover priority behavior with solver tests.
- [Existing persisted teachers might accidentally opt in] -> Use a non-null migration default and explicitly backfill `false`.

## Migration Plan

1. Add the non-null teacher boolean through a new Alembic migration with a default of `false`, backfilling current rows.
2. Deploy the backend contracts and scheduler behavior with the default disabled, preserving existing schedules.
3. Deploy the frontend toggle and preview display.
4. Roll back application behavior by ignoring the field; a database downgrade removes the field after dependent application versions are no longer running.
