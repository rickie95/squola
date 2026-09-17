# Matters

1. a subject matters has a name (History, Geography, Maths, Science)
2. a subject matter can be teached by one or more Teachers,
3. class has a single teacher teaching that subject matter, eg "In 2B History is teached only by Mr Jones"
4. a matter has a fixed number of hours per week, cannot be more or less than that number
5. a matter can have a set of tags or requirements that are transmitted by default to an assignment.

## Requirements
1. some matters might require additional constraints, like "no more than two hours of this matter in a day", or "at least two lessons per week"
2. the daily limit is a total over the day, not the length of a single lesson: two consecutive hours plus a later one is still three hours in that day
3. a matter's default requirements are transmitted to its assignments as a delta. Adding a default adds it to the assignments that already exist, removing a default removes it from them, and a requirement set on one assignment alone survives both
4. a combination that can never be scheduled is refused when it is written, not when the timetable is generated
