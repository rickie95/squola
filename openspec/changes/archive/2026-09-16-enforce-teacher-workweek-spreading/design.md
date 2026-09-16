## Context

See `proposal.md` for motivation. The current daily workload constraint permits
0 or 2 to 5 lessons on every weekday, so it does not spread a standard
teacher's timetable. Fixed unavailability blocks individual periods. The
existing flexible preference only minimizes a violation when all five
weekdays are used and can therefore be relaxed.

## Goals / Non-Goals

**Goals:**
- Make every non-blocked weekday a required teaching day for a standard
  teacher.
- Model a flexible day as a hard, solver-selected full-day unavailability.
- Maximize teaching weekdays for flexible teachers after preserving at least
  one free weekday.
- Keep fixed whole-day unavailability and flexible requests mutually
  exclusive across UI and API callers.

**Non-Goals:**
- Adding a separate external-employment attribute.
- Allowing a user to select the flexible weekday.
- Restoring a cleared flexible request when a full-day block is removed.
- Changing the existing 2 to 5 lesson legal daily workload range.

## Decisions

### Derive full-day blocks from existing unavailability records

A weekday is fully hard-blocked only when the teacher has an unavailable
record for each configured teaching period on that weekday. No schema change
is needed: the existing slot-level records remain the source of truth.

This is preferred to a duplicated `unavailable_day` field, which could drift
from the individual slots. Treating any partial blackout as a day off was
rejected because it would discard a day that remains usable and conflict with
the workweek-spreading policy.

### Enforce daily workloads by teacher mode

For a standard teacher, each non-fully-blocked weekday must contain 2 to 5
lessons. Fully blocked weekdays already have all lesson variables forced to
zero by the unavailability constraint.

For a teacher with a flexible request, retain zero-or-2-to-5 as the daily
domain, create exact workday indicators, and constrain the total working days
to at most four. Link each indicator bidirectionally to that day's lesson
total so a workday cannot be reported without a lesson and a scheduled lesson
cannot be omitted from the count.

This makes the day off hard. Allowing a fifth teaching day for high workloads
was rejected because it would schedule a teacher during the requested
unavailability. Requiring exactly four teaching days was rejected because a
low weekly load may be unable to meet the two-lesson daily minimum four times.

### Maximize flexible teachers' workdays before timing preferences

For a flexible teacher, maximize the number of true workday indicators while
the at-most-four constraint remains hard. Combine this with existing timing
and gap preferences using a calculated dominant coefficient, so gaining a
feasible teaching weekday outweighs every secondary preference term.

This prevents a low-load flexible teacher from being concentrated into fewer
days than necessary. A separate solve phase was rejected because it would
complicate time-limit handling and feasible-but-not-optimal results.

### Enforce mutual exclusion at the API boundary and guide in the UI

When adding the final unavailable period that completes a weekday, clear
`prefers_day_off` in the same transaction. Reject a request that enables the
setting while any weekday is fully hard-blocked. The frontend detects both
states to disable invalid controls and explain why the setting was cleared or
cannot be enabled.

UI-only enforcement was rejected because direct API clients could otherwise
produce contradictory persisted state. Automatically removing a hard
unavailability to enable a flexible request was rejected because it could
silently discard an external-school commitment.

## Risks / Trade-offs

- [Normal teachers with fewer than 10 weekly lessons become infeasible] ->
  Preview and generation errors must identify the workweek distribution cause.
- [A partial blackout leaves too few periods to schedule the daily minimum] ->
  Retain it as an eligible weekday and report ordinary infeasibility rather
  than silently treating it as fully blocked.
- [A flexible teacher with more than 20 weekly lessons becomes infeasible] ->
  Surface that the hard flexible day leaves only four teaching weekdays.
- [Sequential slot requests briefly approach a full-day block] -> Clear the
  flexible setting only when the final period completes the full-day block.

## Migration Plan

1. Deploy backend validation and automatic clearing before frontend controls.
2. Deploy the solver and preview validation with the updated workload rules.
3. Deploy the frontend explanations and disabled states.
4. Roll back by restoring the existing daily-domain behavior; no database
   migration is required because the existing preference and unavailability
   data remain valid.
