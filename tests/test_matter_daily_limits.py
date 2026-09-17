"""Daily cap on how many hours of one matter-class assignment land in one day."""

from test_teacher_daily_workload import make_data, solve


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
