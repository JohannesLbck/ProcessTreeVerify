 # Verification Methods
Activity labels, resources and data names are strings. Time values are seconds or descriptive strings.

## Control Flow
- `exists(tree, a)`: element|None — is activity `a` present?
- `absence(tree, a)`: bool — `a` absent?
- `loop(tree, a)`: element|None — `a` in a loop?
- `directly_follows(tree, a, b)`: bool — `b` follows `a` immediately.
- `leads_to(tree, a, b)`: bool — `a` occurs before `b` (ordering).
- `precedence(tree, a, b)`: bool — `b` must occur before `a`.
- `leads_to_absence(tree, a, b)`: bool — `a` exists and `b` does not occur after it.
- `precedence_absence(tree, a, b)`: bool — `a` exists and `b` does not occur before it.
- `parallel(tree, a, b)`: bool — `a` and `b` are parallel.

## Resource
- `executed_by_identify(tree, resource)`: label|None — find activity for `resource`.
- `executed_by(tree, a, resource)`: bool — `a` executed by `resource`?
- `executed_by_return(tree, a)`: resource|None — first resource executing `a`.

## Time
- `timed_alternative(tree, a, b, time)`: bool — `b` acts as timeout alternative to `a`.
- `min_time_between(tree, a, b, time, c=None)`: bool — enforce minimum delay (optional alternative `c`).
- `max_time_between(tree, a, b, time, c=None)`: bool — enforce maximum delay (optional alternative `c`).
- `by_due_date(tree, a, timestamp, c=None)`: bool — unified due-date check (optional alternative `c`).
- `recurring(tree, a, t)`: bool — `a` recurs every `t` in a loop.

## Data
- `send_exist(tree, data)`: list|None — list of activities sending `data`.
- `receive_exist(tree, data)`: list|None — list of activities receiving `data`.
- `activity_sends(tree, a, data)`: bool — `a` sends `data`.
- `activity_receives(tree, a, data)`: bool — `a` receives `data`.
- `condition_directly_follows(tree, condition, a)`: bool — `a` directly follows when `condition` holds.
- `condition_eventually_follows(tree, condition, a, scope="branch")`: bool — `a` eventually follows `condition` (scope `branch` or `global`).
- `data_leads_to_absence(tree, condition, a)`: bool — `condition` should not lead to `a`.

## Failure
- `failure_eventually_follows(tree, a, b)`: bool — `b` follows if `a` fails (rescue handling).
- `failure_directly_follows(tree, a, b)`: bool — `b` directly follows failure of `a`.