"""Schedule appliance runs against an hourly weekday profile."""
from copy import deepcopy
from math import isfinite


STATUSES = ["Planned", "Running", "Done"]


def add_task_load(load, task, start):
    # Convert total run energy (kWh) into constant average power (kW).
    power = task["kwh"] * 60 / task["minutes"]
    for minute in range(start, start + task["minutes"]):
        load[minute] += power


def plan_day(profile, tasks, not_before=0, *, earliest_start=False):
    if len(profile) != 24 or any(not isfinite(v) or v < 0 for v in profile):
        raise ValueError("A complete, non-negative 24-hour demand profile is required.")
    if type(not_before) is not int or not 0 <= not_before <= 1440:
        raise ValueError("The earliest planning time must be within the day.")
    if len(tasks) > 30:
        raise ValueError("Plan up to 30 appliance runs per day.")
    # Work on a copy so trying a schedule leaves the original task list untouched.
    planned = deepcopy(tasks)
    seen = set()
    for task in planned:
        if task["id"] in seen or task["after"] not in seen | {None}:
            raise ValueError("Task order links must refer to an earlier task.")
        seen.add(task["id"])
        if (type(task["minutes"]) is not int or not 1 <= task["minutes"] <= 1440
                or not isfinite(task["kwh"]) or not 0 < task["kwh"] <= 100
                or type(task["earliest"]) is not int or type(task["deadline"]) is not int
                or not 0 <= task["earliest"] < task["deadline"] <= 1440
                or task["status"] not in STATUSES):
            raise ValueError("Check the run time, energy, and allowed window.")
        task["reason"] = ""
        if task["status"] == "Planned":
            task["start"] = None
        elif (type(task["start"]) is not int
              or not task["earliest"] <= task["start"]
              <= task["deadline"] - task["minutes"]):
            raise ValueError("A running or completed task needs a valid scheduled start.")

    # Repeat each hourly estimate for 60 minutes to place runs of any duration.
    load = [float(v) for v in profile for _ in range(60)]
    scheduled = {}

    # Keep running and completed tasks fixed while rescheduling pending ones.
    for task in planned:
        if task["status"] != "Planned":
            add_task_load(load, task, task["start"])
            scheduled[task["id"]] = task

    # shortcut: greedy placement handles a small household list; use an optimizer for global guarantees.
    pending = [task for task in planned if task["status"] == "Planned"]
    while pending:
        ready = [task for task in pending if task["after"] is None
                 or task["after"] not in {other["id"] for other in pending}]
        # Place the least flexible ready task first; higher energy breaks a tie.
        task = min(ready, key=lambda t: (
            t["deadline"] - t["earliest"] - t["minutes"], -t["kwh"],
        ))
        pending.remove(task)
        parent = scheduled.get(task["after"])
        if task["after"] is not None and parent is None:
            task["reason"] = "The earlier task needs a time first. Widen its window."
            continue
        earliest = max(task["earliest"], not_before,
                       parent["start"] + parent["minutes"] if parent else 0)
        candidates = []
        # Starts use quarter-hours; the last minute of a short run is kept exact.
        for start in range(((earliest + 14) // 15) * 15,
                           task["deadline"] - task["minutes"] + 1, 15):
            end = start + task["minutes"]
            if any(other["appliance"] == task["appliance"]
                   and start < other["start"] + other["minutes"]
                   and end > other["start"] for other in scheduled.values()):
                continue
            if earliest_start:
                candidates.append(((start,), start))
                break
            candidate = load.copy()
            add_task_load(candidate, task, start)
            # Prefer the lowest daily peak, then a smoother load, then an earlier start.
            candidates.append(((max(candidate), sum(v * v for v in candidate), start), start))
        if not candidates:
            task["reason"] = "No time fits. Widen the window or shorten the run."
            continue
        task["start"] = min(candidates)[1]
        add_task_load(load, task, task["start"])
        scheduled[task["id"]] = task
    return planned, load
