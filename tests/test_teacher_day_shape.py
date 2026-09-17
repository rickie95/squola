"""How a teacher's hours are laid out inside a day: contiguity, gaps, runs."""

import pytest

from squola.models import (
    ClassMatterAssignment,
    Matter,
    SchedulePreference,
    SchoolClass,
    Teacher,
    TeacherUnavailability,
)
from squola.scheduler import (
    W_GAP,
    W_LONG_RUN,
    W_TIME_PREFERENCE,
    ScheduleGenerator,
    SchedulingData,
    compute_quality_metrics,
    daily_band,
)


def make_data(
    assignments: list[tuple[int, int]],
    *,
    unavailable_days: set[int] | None = None,
    preference: str = SchedulePreference.NONE.value,
    prefers_day_off: bool = False,
) -> SchedulingData:
    """Build one teacher from (class_id, hours_per_week) pairs."""
    teacher = Teacher(
        id=1,
        workspace_id=1,
        first_name="Azzurra",
        last_name="Lami",
        schedule_preference=preference,
        prefers_day_off=prefers_day_off,
    )
    classes = {
        class_id: SchoolClass(
            id=class_id, workspace_id=1, year="I", section=chr(ord("A") + class_id - 1)
        )
        for class_id, _ in assignments
    }
    built = []
    for index, (class_id, hours_per_week) in enumerate(assignments, start=1):
        matter = Matter(id=index, workspace_id=1, name=f"Matter {index}")
        built.append(
            ClassMatterAssignment(
                id=index,
                workspace_id=1,
                class_id=class_id,
                matter_id=matter.id,
                teacher_id=teacher.id,
                hours_per_week=hours_per_week,
                requirements=[],
                teacher=teacher,
                school_class=classes[class_id],
                matter=matter,
            )
        )

    return SchedulingData(
        teachers=[teacher],
        classes=list(classes.values()),
        assignments=built,
        unavailabilities=[
            TeacherUnavailability(
                id=day * 10 + hour,
                workspace_id=1,
                teacher_id=teacher.id,
                day_of_week=day,
                hour_slot=hour,
            )
            for day in unavailable_days or set()
            for hour in range(1, 7)
        ],
        fixed_lessons=[],
    )


def solve_with_metrics(data: SchedulingData, time_limit_seconds: float = 10.0):
    generator = ScheduleGenerator(data)
    generator.build_model()
    schedule = generator.solve(time_limit_seconds=time_limit_seconds)
    metrics = compute_quality_metrics(schedule.slots, generator.eligible_workdays)
    return schedule, metrics


def hours_by_class(schedule, day: int) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for slot in schedule.slots:
        if slot.day == day:
            result.setdefault(slot.class_id, []).append(slot.hour)
    return {class_id: sorted(hours) for class_id, hours in result.items()}


# --- 2.1 weight calibration -------------------------------------------------


def test_long_run_outweighs_taking_the_break():
    """Otherwise a teacher with a time preference keeps the four-hour run."""
    assert W_LONG_RUN > W_GAP + 2 * W_TIME_PREFERENCE


# --- 2.3 / 2.4 preferences --------------------------------------------------


def test_early_preference_still_takes_the_first_hours():
    schedule, _ = solve_with_metrics(
        make_data(
            [(1, 2)],
            unavailable_days={1, 2, 3, 4},
            preference=SchedulePreference.EARLY.value,
        )
    )

    assert schedule.status == "OPTIMAL"
    assert sorted(slot.hour for slot in schedule.slots) == [1, 2]


@pytest.mark.parametrize(
    "preference",
    [
        SchedulePreference.NONE.value,
        SchedulePreference.MINIMIZE_GAPS.value,
        SchedulePreference.MAXIMIZE_GAPS.value,
        SchedulePreference.EARLY.value,
        SchedulePreference.LATE.value,
    ],
)
def test_day_shape_applies_to_every_preference(preference: str):
    """
    Including no preference at all, which used to contribute no objective, and
    the time preferences, which must not buy an earlier slot with a class switch.
    """
    _, metrics = solve_with_metrics(
        make_data([(1, 2), (2, 2)], unavailable_days={1, 2, 3, 4}, preference=preference)
    )

    assert metrics["class_blocks"] == 0


# --- 3.1 / 3.2 class contiguity ---------------------------------------------


def test_alternating_classes_are_not_generated():
    """The Lami case: 3C 2C 3C 2C in a single morning."""
    schedule, metrics = solve_with_metrics(
        make_data([(1, 2), (2, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert schedule.status == "OPTIMAL"
    assert metrics["class_blocks"] == 0
    for hours in hours_by_class(schedule, day=0).values():
        assert hours == list(range(hours[0], hours[0] + 2))


def test_two_matters_in_one_class_are_a_single_block():
    """The teacher does not move and the class does not change teacher."""
    schedule, metrics = solve_with_metrics(
        make_data([(1, 2), (1, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert schedule.status == "OPTIMAL"
    assert metrics["class_blocks"] == 0
    assert metrics["gap_hours"] == 0
    hours = sorted(slot.hour for slot in schedule.slots)
    assert hours == list(range(hours[0], hours[0] + 4))


# --- 3.3 / 3.4 gaps ---------------------------------------------------------


def test_two_hours_of_one_class_are_joined():
    """The Ancarani case: 3B - - 3B on a Friday."""
    schedule, metrics = solve_with_metrics(
        make_data([(1, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert schedule.status == "OPTIMAL"
    assert metrics["gap_hours"] == 0
    assert metrics["class_blocks"] == 0


def test_free_hours_at_the_edges_of_the_day_are_not_gaps():
    data = make_data([(1, 2)], unavailable_days={1, 2, 3, 4})
    generator = ScheduleGenerator(data)
    generator.build_model()
    schedule = generator.solve(time_limit_seconds=10.0)

    # Lessons sit somewhere inside a six-hour day, never at both edges.
    assert compute_quality_metrics(schedule.slots, {1: 5})["gap_hours"] == 0

    edges = [slot for slot in schedule.slots]
    edges[0].hour, edges[1].hour = 1, 6
    assert compute_quality_metrics(edges, {1: 5})["gap_hours"] == 4


# --- 3.5 long runs ----------------------------------------------------------


def test_four_hour_day_takes_a_break():
    _, metrics = solve_with_metrics(
        make_data([(1, 2), (2, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert metrics["long_runs"] == 0
    assert metrics["gap_hours"] == 1


def test_five_hour_day_takes_a_break():
    _, metrics = solve_with_metrics(
        make_data([(1, 3), (2, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert metrics["long_runs"] == 0
    assert metrics["gap_hours"] == 1


def test_three_hour_day_stays_contiguous():
    schedule, metrics = solve_with_metrics(
        make_data([(1, 3)], unavailable_days={1, 2, 3, 4})
    )

    assert metrics["gap_hours"] == 0
    hours = sorted(slot.hour for slot in schedule.slots)
    assert hours == list(range(hours[0], hours[0] + 3))


# --- 4.1 / 4.2 / 4.3 / 4.5 weekly balance -----------------------------------


@pytest.mark.parametrize(
    ("total", "workdays", "expected"),
    [(18, 5, (3, 4)), (12, 4, (3, 3)), (20, 5, (4, 4)), (8, 4, (2, 2))],
)
def test_daily_band_is_derived_from_the_teacher_hours(
    total: int, workdays: int, expected: tuple[int, int]
):
    assert daily_band(total, workdays) == expected


def test_weekly_load_is_spread_instead_of_concentrated():
    """18 hours become 4,4,4,3,3 rather than 5,5,4,2,2.

    Six interchangeable classes leave CP-SAT unable to prove optimality within
    any useful budget, while the optimum itself is reached in under a second -
    so this asserts the solution, not the status.
    """
    schedule, metrics = solve_with_metrics(
        make_data([(c, 3) for c in range(1, 7)]), time_limit_seconds=2.0
    )

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    loads = sorted(
        sum(1 for slot in schedule.slots if slot.day == day) for day in range(5)
    )
    assert loads == [3, 3, 4, 4, 4]
    assert metrics["balance_deviation"] == 0


def test_flexible_day_off_spreads_over_the_remaining_weekdays():
    schedule, metrics = solve_with_metrics(
        make_data([(c, 3) for c in range(1, 5)], prefers_day_off=True)
    )

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    loads = [sum(1 for slot in schedule.slots if slot.day == day) for day in range(5)]
    assert sorted(loads) == [0, 3, 3, 3, 3]
    assert metrics["balance_deviation"] == 0
