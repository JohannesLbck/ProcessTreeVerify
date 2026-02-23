# Verification Methods Documentation

This document provides documentation for the methods in `annotated_verification.py`. The file contains functions for verifying process compliance based on control flow, resources, time, and data constraints in XML-based process Trees.

## Control Flow Methods

### exists(tree, a)
Checks if an activity `a` exists in the XML tree and returns the element or None. Identifies activities by label.

**Parameters:**
- `tree`: The XML tree (ElementTree root).
- `a`: Activity label or Element.

**Returns:** Element if found, None otherwise.

### absence(tree, a)
Opposite of exists; returns True if activity `a` does not exist.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.

**Returns:** Boolean.

### loop(tree, a)
Checks if activity `a` is in a loop and returns the loop element or None.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.

**Returns:** Loop element or None.

### directly_follows(tree, a, b)
Checks if activity `b` directly follows activity `a` in the process flow.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.

**Returns:** Boolean.

### leads_to(tree, a, b)
Checks if activity `a` leads to activity `b` (i.e., `a` occurs before `b`).

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.

**Returns:** Boolean.

### precedence(tree, a, b)
Checks if activity `b` precedes activity `a` (i.e., `b` must occur before `a`).

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.

**Returns:** Boolean.

### leads_to_absence(tree, a, b)
Checks if activity `a` exists and activity `b` does not exist after it.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.

**Returns:** Boolean.

### precedence_absence(tree, a, b)
Checks if activity `a` exists and activity `b` does not exist before it.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.

**Returns:** Boolean.

### parallel(tree, a, b)
Checks if activities `a` and `b` are in parallel.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.

**Returns:** Boolean.

## Resource Methods

### executed_by_identify(tree, resource)
Returns the label of the activity executed by the given resource, or None.

**Parameters:**
- `tree`: The XML tree.
- `resource`: Resource name.

**Returns:** Activity label or None.

### executed_by(tree, a, resource)
Checks if activity `a` is executed by the given resource based on annotations.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `resource`: Resource name.

**Returns:** Boolean.

### executed_by_return(tree, a)
Returns the first resource executing activity `a`.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.

**Returns:** Resource name or None.

## Time Methods

### timed_alternative(tree, a, b, time)
Checks if activities `a` and `b` are in a timed alternative relationship with the given timeout. This ensures that if `a` takes too long to be executed, `b` is executed as an alternative. For example if a process should terminate if an activity `a` takes too long, then `b` is a terminate.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.
- `time`: Timeout value.

**Returns:** Boolean.

### min_time_between(tree, a, b, time, c=None)
Enforces a minimum time between activities `a` and `b`, optionally with alternative `c`.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.
- `time`: Minimum time.
- `c`: Optional alternative activity.

**Returns:** Boolean.

### by_due_date(tree, a, timestamp, c=None)
Checks due date enforcement, first via explicit means then via annotation, optionally with alternative `c`.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `timestamp`: Due date timestamp.
- `c`: Optional alternative activity.

**Returns:** Boolean.

### max_time_between(tree, a, b, time, c=None)
Enforces a maximum time between activities `a` and `b`, optionally with alternative `c`.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `b`: Activity label.
- `time`: Maximum time.
- `c`: Optional alternative activity.

**Returns:** Boolean.

### recurring(tree, a, t)
Checks if activity `a` recurs at the specified time t interval within a loop.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `t`: Time interval for recurrence.

**Returns:** Boolean.

## Data Methods

### send_exist(tree, data, complete=False)
Checks if any activity sends the given data object and returns activity element(s) or None.

**Parameters:**
- `tree`: The XML tree.
- `data`: Data object name.
- `complete`: Optional boolean (default False). If False, returns the first matching element. If True, returns the list of all matching elements.

**Returns:** First activity element if `complete=False`, list of activity elements if `complete=True`, or None if not found.

### receive_exist(tree, data, complete=False)
Checks if any activity receives the given data object and returns activity element(s) or None.

**Parameters:**
- `tree`: The XML tree.
- `data`: Data object name.
- `complete`: Optional boolean (default False). If False, returns the first matching element. If True, returns the list of all matching elements.

**Returns:** First activity element if `complete=False`, list of activity elements if `complete=True`, or None if not found.

### activity_sends(tree, a, data)
Checks if activity `a` sends the given data object.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `data`: Data object name.

**Returns:** Boolean.

### activity_receives(tree, a, data)
Checks if activity `a` receives the given data object.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label.
- `data`: Data object name.

**Returns:** Boolean.

### condition(tree, condition)
Checks if the given condition exists in the process.

**Parameters:**
- `tree`: The XML tree.
- `condition`: Condition string.

**Returns:** Boolean.

### condition_directly_follows(tree, condition, a)
Checks if activity (or a subtree)`a` directly follows when a given condition is satisfied.

**Parameters:**
- `tree`: The XML tree.
- `condition`: Condition string.
- `a`: Activity label.

**Returns:** Boolean.

### condition_eventually_follows(tree, condition, a, scope="branch")
Checks if activity (or a subtree)`a` eventually follows the given condition. By default the scope is branch as in it follows if and only if condition is satisfied.
Changing the scope to global makes it so that the activity can follow also if the condition is not satisfied.

**Parameters:**
- `tree`: The XML tree.
- `condition`: Condition string.
- `a`: Activity label.
- `scope`: "branch" or "global".

**Returns:** Boolean.

### data_leads_to_absence(tree, condition, a)
Checks if the condition does not lead to activity `a`.

**Parameters:**
- `tree`: The XML tree.
- `condition`: Condition string.
- `a`: Activity label.

**Returns:** Boolean.

## Failure Handling Methods

### failure_eventually_follows(tree, a, b)
Checks if activity `b` eventually follows when activity `a` fails by examining rescue data objects and their usage in branch conditions.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label that may fail.
- `b`: Activity label that should follow the failure.

**Returns:** Boolean.

### failure_directly_follows(tree, a, b)
Checks if activity `b` directly follows when activity `a` fails by examining rescue data objects and their usage in branch conditions.

**Parameters:**
- `tree`: The XML tree.
- `a`: Activity label that may fail.
- `b`: Activity label that should directly follow the failure.

**Returns:** Boolean.