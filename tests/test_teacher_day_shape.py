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
    ScheduleSlot,
    W_BREAK_DAY,
    W_BREAK_DAY_STRICT,
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
    metrics = compute_quality_metrics(
        schedule.slots, generator.eligible_workdays, generator.unavailable
    )
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
    assert W_LONG_RUN > W_BREAK_DAY + 2 * W_TIME_PREFERENCE


def test_grouping_preference_sits_between_the_four_and_five_hour_gains():
    """
    Below the four-hour gain it would behave exactly like no preference at all;
    above the five-hour gain it would keep five hours in a row, which nobody
    asked for.
    """
    assert W_LONG_RUN < W_BREAK_DAY_STRICT + 2 * W_TIME_PREFERENCE < 2 * W_LONG_RUN


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
    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 0
    hours = sorted(slot.hour for slot in schedule.slots)
    assert hours == list(range(hours[0], hours[0] + 4))


# --- 3.3 / 3.4 gaps ---------------------------------------------------------


def test_two_hours_of_one_class_are_joined():
    """The Ancarani case: 3B - - 3B on a Friday."""
    schedule, metrics = solve_with_metrics(
        make_data([(1, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert schedule.status == "OPTIMAL"
    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 0
    assert metrics["class_blocks"] == 0


def test_free_hours_at_the_edges_of_the_day_are_not_gaps():
    data = make_data([(1, 2)], unavailable_days={1, 2, 3, 4})
    generator = ScheduleGenerator(data)
    generator.build_model()
    schedule = generator.solve(time_limit_seconds=10.0)

    # Lessons sit somewhere inside a six-hour day, never at both edges.
    assert compute_quality_metrics(schedule.slots, {1: 5})["excess_gap_hours"] == 0

    edges = [slot for slot in schedule.slots]
    edges[0].hour, edges[1].hour = 1, 6
    assert compute_quality_metrics(edges, {1: 5})["excess_gap_hours"] == 4


# --- 3.5 long runs ----------------------------------------------------------


def test_four_hour_day_takes_a_break():
    _, metrics = solve_with_metrics(
        make_data([(1, 2), (2, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert metrics["long_runs"] == 0
    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 1


def test_five_hour_day_takes_a_break():
    _, metrics = solve_with_metrics(
        make_data([(1, 3), (2, 2)], unavailable_days={1, 2, 3, 4})
    )

    assert metrics["long_runs"] == 0
    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 1


def test_three_hour_day_stays_contiguous():
    schedule, metrics = solve_with_metrics(
        make_data([(1, 3)], unavailable_days={1, 2, 3, 4})
    )

    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 0
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


# --- unavailability is not a gap --------------------------------------------


def test_unavailable_slot_between_two_lessons_is_not_a_gap():
    """The teacher is not at school and is not waiting."""
    metrics = compute_quality_metrics(
        _slots_at(day=0, hours=[2, 4]), {1: 5}, unavailable={(1, 0, 3)}
    )

    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 0


def test_free_slot_next_to_an_unavailable_one_is_still_a_gap():
    """Only the hour the teacher could have taught in counts."""
    metrics = compute_quality_metrics(
        _slots_at(day=0, hours=[1, 5]), {1: 5}, unavailable={(1, 0, 3), (1, 0, 4)}
    )

    assert metrics["excess_gap_hours"] == 1


def test_solver_does_not_pay_for_a_gap_it_cannot_avoid():
    """
    Two hours either side of a blocked middle hour: the day is legal and carries
    no excess, so the teacher is not pushed onto another arrangement.
    """
    data = make_data([(1, 2), (2, 2)], unavailable_days={1, 2, 3, 4})
    data.unavailabilities = [
        unavailability
        for unavailability in data.unavailabilities
        if unavailability.day_of_week != 0
    ] + [
        TeacherUnavailability(
            id=900 + hour, workspace_id=1, teacher_id=1, day_of_week=0, hour_slot=hour
        )
        for hour in (1, 2)
    ]

    schedule, metrics = solve_with_metrics(data)

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    assert metrics["excess_gap_hours"] == 0


# --- the allowance belongs to long days -------------------------------------


def test_short_day_gets_no_gap_at_all():
    """A three-hour day does not earn the break."""
    _, metrics = solve_with_metrics(make_data([(1, 3)], unavailable_days={1, 2, 3, 4}))

    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 0


def test_reduced_hours_teacher_gets_a_week_without_gaps():
    """
    Eight weekly hours over four days are two-hour days, which never earn the
    allowance - the proportionality falls out of the day length alone.
    """
    schedule, metrics = solve_with_metrics(
        make_data([(1, 4), (2, 4)], prefers_day_off=True)
    )

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    assert len(schedule.slots) == 8
    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 0


def test_no_day_ever_exceeds_its_allowance():
    """The absolute rule, over a full five-day week."""
    schedule, metrics = solve_with_metrics(
        make_data([(1, 5), (2, 5), (3, 5), (4, 3)])
    )

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    assert metrics["excess_gap_hours"] == 0
    for day in range(5):
        hours = sorted(slot.hour for slot in schedule.slots if slot.day == day)
        if len(hours) > 1:
            gaps = (hours[-1] - hours[0] + 1) - len(hours)
            assert gaps <= 1, f"day {day} has {gaps} gap hours: {hours}"


# --- preferences act on the week --------------------------------------------


def test_grouping_preference_keeps_the_four_hour_day_contiguous():
    schedule, metrics = solve_with_metrics(
        make_data(
            [(1, 2), (2, 2)],
            unavailable_days={1, 2, 3, 4},
            preference=SchedulePreference.MINIMIZE_GAPS.value,
        )
    )

    assert metrics["break_days"] == 0
    hours = sorted(slot.hour for slot in schedule.slots)
    assert hours == list(range(hours[0], hours[0] + 4))


def test_grouping_preference_still_breaks_the_five_hour_day():
    _, metrics = solve_with_metrics(
        make_data(
            [(1, 3), (2, 2)],
            unavailable_days={1, 2, 3, 4},
            preference=SchedulePreference.MINIMIZE_GAPS.value,
        )
    )

    assert metrics["break_days"] == 1
    assert metrics["long_runs"] == 0


def test_time_preference_still_buys_the_four_hour_break():
    """
    The case the old assert claimed to guarantee and did not: with the weight
    modulated by a grouping preference the break stopped paying off.
    """
    _, metrics = solve_with_metrics(
        make_data(
            [(1, 2), (2, 2)],
            unavailable_days={1, 2, 3, 4},
            preference=SchedulePreference.EARLY.value,
        )
    )

    assert metrics["break_days"] == 1
    assert metrics["long_runs"] == 0


def test_distribution_preference_spreads_the_break_over_the_week():
    schedule, metrics = solve_with_metrics(
        make_data(
            [(1, 5), (2, 5), (3, 5), (4, 5)],
            preference=SchedulePreference.MAXIMIZE_GAPS.value,
        ),
        time_limit_seconds=20.0,
    )

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    assert metrics["excess_gap_hours"] == 0
    # Four-hour days all week: every one of them should carry its own break
    # rather than the week concentrating gaps into a single day.
    assert metrics["break_days"] >= 4


def test_distribution_preference_never_exceeds_the_allowance():
    schedule, metrics = solve_with_metrics(
        make_data(
            [(1, 4), (2, 4)],
            prefers_day_off=True,
            preference=SchedulePreference.MAXIMIZE_GAPS.value,
        )
    )

    assert schedule.status in ("OPTIMAL", "FEASIBLE")
    assert metrics["excess_gap_hours"] == 0
    assert metrics["break_days"] == 0  # two-hour days earn no allowance


@pytest.mark.parametrize(
    "preference",
    [
        SchedulePreference.NONE.value,
        SchedulePreference.MINIMIZE_GAPS.value,
        SchedulePreference.MAXIMIZE_GAPS.value,
    ],
)
def test_gap_preferences_do_not_touch_class_contiguity(preference: str):
    """Grouping and distribution say nothing about how classes are grouped."""
    _, metrics = solve_with_metrics(
        make_data([(1, 2), (2, 2)], unavailable_days={1, 2, 3, 4}, preference=preference)
    )

    assert metrics["class_blocks"] == 0


def _slots_at(day: int, hours: list[int]) -> list[ScheduleSlot]:
    return [
        ScheduleSlot(
            day=day,
            hour=hour,
            class_id=1,
            class_name="IA",
            matter_id=1,
            matter_name="Matematica",
            teacher_id=1,
            teacher_name="Azzurra Lami",
            assignment_id=1,
        )
        for hour in hours
    ]
