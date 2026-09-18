"""Daily cap on how many hours of one matter-class assignment land in one day."""

import pytest

from squola.models import FixedClassLesson, MatterRequirements as R
from squola.scheduler import (
    MAX_DAILY_ASSIGNMENT_HOURS,
    requirement_conflict,
    resolve_daily_cap,
)
from test_teacher_daily_workload import make_data, solve


@pytest.mark.parametrize(
    "requirements, expected",
    [
        ([], MAX_DAILY_ASSIGNMENT_HOURS),
        (None, MAX_DAILY_ASSIGNMENT_HOURS),
        ([R.AT_LEAST_TWICE_PER_WEEK], MAX_DAILY_ASSIGNMENT_HOURS),
        ([R.MAX_TWO_HOURS_PER_DAY], 2),
        ([R.MAX_ONE_HOUR_PER_DAY], 1),
        ([R.MAX_ONE_HOUR_PER_DAY, R.MAX_TWO_HOURS_PER_DAY], 1),
        ([R.MAX_TWO_HOURS_PER_DAY, R.MAX_ONE_HOUR_PER_DAY], 1),
    ],
    ids=["empty", "none", "other-req", "two", "one", "both", "both-reversed"],
)
def test_resolve_daily_cap(requirements, expected):
    assert resolve_daily_cap(requirements) == expected


def test_four_hours_of_one_assignment_in_a_day_is_infeasible():
    """3 + gap + 1 of the same matter in a day used to pass the old window rule."""
    schedule = solve(make_data([4], unavailable_days={1, 2, 3, 4}))

    assert schedule.status == "INFEASIBLE"


def test_three_hours_of_one_assignment_in_a_day_is_allowed():
    schedule = solve(make_data([3], unavailable_days={1, 2, 3, 4}))

    assert schedule.status == "OPTIMAL"
    assert len(schedule.slots) == 3
    assert {slot.day for slot in schedule.slots} == {0}


def test_three_hours_on_two_consecutive_days_is_allowed():
    schedule = solve(make_data([6], unavailable_days={2, 3, 4}))

    assert schedule.status == "OPTIMAL"
    hours_by_day = {}
    for slot in schedule.slots:
        hours_by_day[slot.day] = hours_by_day.get(slot.day, 0) + 1
    assert hours_by_day == {0: 3, 1: 3}


def test_weekly_hours_beyond_the_cap_are_infeasible():
    """Five weekdays at three hours each leave no room for a sixteenth hour."""
    schedule = solve(make_data([16]))

    assert schedule.status == "INFEASIBLE"


def test_fifteen_weekly_hours_still_fit():
    schedule = solve(make_data([15]))

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    assert len(schedule.slots) == 15


def capped(data, *requirements, assignment_index: int = 0):
    """Declare cap requirements on one of make_data's assignments."""
    data.assignments[assignment_index].requirements = list(requirements)
    return data


def test_three_hours_in_a_day_is_infeasible_under_a_two_hour_cap():
    """Monday is the only workday, so the cap is the only thing that can fail."""
    data = capped(
        make_data([3], unavailable_days={1, 2, 3, 4}), R.MAX_TWO_HOURS_PER_DAY
    )

    assert solve(data).status == "INFEASIBLE"


def test_the_cap_counts_the_daily_total_not_the_run_length():
    """
    Two consecutive hours plus a third one after a gap is three hours in a day.
    A cap on run length would allow this shape; a cap on the daily total does not.
    """
    fixed = [
        FixedClassLesson(
            id=hour,
            workspace_id=1,
            class_id=1,
            assignment_id=1,
            day_of_week=0,
            hour_slot=hour,
        )
        for hour in (1, 2, 4)
    ]

    def monday_only():
        return make_data([3], unavailable_days={1, 2, 3, 4}, fixed_lessons=fixed)

    assert solve(monday_only()).status == "OPTIMAL"

    assert solve(capped(monday_only(), R.MAX_TWO_HOURS_PER_DAY)).status == "INFEASIBLE"


def test_six_hours_under_a_two_hour_cap_spread_over_at_least_three_days():
    data = capped(make_data([6], unavailable_days={3, 4}), R.MAX_TWO_HOURS_PER_DAY)

    schedule = solve(data)

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    assert len(schedule.slots) == 6
    hours_by_day = {}
    for slot in schedule.slots:
        hours_by_day[slot.day] = hours_by_day.get(slot.day, 0) + 1
    assert len(hours_by_day) >= 3
    assert max(hours_by_day.values()) <= 2


def test_weekly_hours_beyond_a_tightened_cap_are_infeasible():
    """Twelve hours fit under the default cap of three, never under two."""
    assert solve(make_data([12])).status in ("OPTIMAL", "FEASIBLE")

    data = capped(make_data([12]), R.MAX_TWO_HOURS_PER_DAY)
    assert solve(data).status == "INFEASIBLE"


def test_two_hours_in_a_day_is_infeasible_under_a_one_hour_cap():
    data = capped(
        make_data([2], unavailable_days={1, 2, 3, 4}), R.MAX_ONE_HOUR_PER_DAY
    )

    assert solve(data).status == "INFEASIBLE"


def test_both_cap_requirements_together_behave_as_the_one_hour_cap():
    data = capped(
        make_data([2], unavailable_days={1, 2, 3, 4}),
        R.MAX_TWO_HOURS_PER_DAY,
        R.MAX_ONE_HOUR_PER_DAY,
    )

    assert solve(data).status == "INFEASIBLE"


@pytest.mark.parametrize(
    "requirements, hours_per_week",
    [
        ([R.MAX_ONE_HOUR_PER_DAY, R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK], None),
        ([R.MAX_ONE_HOUR_PER_DAY, R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK], None),
        ([R.MAX_TWO_HOURS_PER_DAY, R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK], None),
        ([R.MAX_ONE_HOUR_PER_DAY], 6),
        ([R.MAX_TWO_HOURS_PER_DAY], 11),
        ([], 16),
    ],
    ids=["one-vs-2h", "one-vs-3h", "two-vs-3h", "one-6h", "two-11h", "default-16h"],
)
def test_requirement_conflict_is_reported(requirements, hours_per_week):
    assert requirement_conflict(requirements, hours_per_week) is not None


@pytest.mark.parametrize(
    "requirements, hours_per_week",
    [
        ([], None),
        ([], 15),
        ([R.MAX_TWO_HOURS_PER_DAY, R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK], 10),
        ([R.MAX_ONE_HOUR_PER_DAY], 5),
        ([R.MAX_ONE_HOUR_PER_DAY, R.MAX_TWO_HOURS_PER_DAY], 5),
        ([R.MAX_ONE_HOUR_PER_DAY, R.AT_LEAST_TWICE_PER_WEEK], 4),
    ],
    ids=["empty", "default-15h", "two-2h-lesson", "one-5h", "both-caps", "twice"],
)
def test_requirement_combination_is_accepted(requirements, hours_per_week):
    assert requirement_conflict(requirements, hours_per_week) is None


def test_weekly_hours_are_only_checked_when_known():
    """A matter declares defaults without knowing any assignment's weekly hours."""
    assert requirement_conflict([R.MAX_ONE_HOUR_PER_DAY]) is None
