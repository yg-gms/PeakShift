import json
from datetime import datetime
from pathlib import Path
import sqlite3
from uuid import uuid4
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from appliances import APPLIANCES, SOURCE
from daily_planner import add_task_load, plan_day
from explore import DATA_FILE, load_hourly
from forecast import build_weekday_profiles
from plan_store import load_plan, save_plan


st.set_page_config(page_title="PeakShift", page_icon="⚡", layout="wide")


@st.cache_data
def load_data():
    hourly = load_hourly(DATA_FILE)
    return build_weekday_profiles(hourly), hourly


def clock(minute):
    return f"{minute // 60:02d}:{minute % 60:02d}"


def persist(updated):
    try:
        save_plan(selected_date, updated, revision)
    except (sqlite3.Error, ValueError, OSError) as error:
        st.error(f"Your changes could not be saved. {error}")
        st.stop()
    st.rerun()


st.title("Plan your appliance use.")
st.write("Add your appliances. Get a daily schedule that spreads out electricity demand.")
st.caption("Sample Swiss household · Times in Europe/Zurich · Plans saved on this computer")
try:
    profiles, hourly = load_data()
except FileNotFoundError:
    st.error("Restore data/household.csv.gz to load the household data.")
    st.stop()

planner, data, evidence = st.tabs(["Your day", "Household data", "What the tests showed"])

with planner:
    now = datetime.now(ZoneInfo("Europe/Zurich"))
    selected_date = st.date_input("Plan for", value=now.date(), key="plan_date")
    profile = profiles.loc[selected_date.weekday()]
    not_before = now.hour * 60 + now.minute + 1 if selected_date == now.date() else 0
    try:
        tasks, revision = load_plan(selected_date)
    except (sqlite3.Error, OSError, json.JSONDecodeError) as error:
        st.error(f"Your saved plan could not be opened. {error}")
        st.stop()

    add, schedule = st.columns([1, 2], gap="large")
    with add:
        st.subheader("Add an appliance")
        appliance = st.selectbox("Appliance", list(APPLIANCES), key="appliance")
        preset = APPLIANCES[appliance]
        st.caption(f"Example run · {preset['minutes']} min · about {preset['kwh']:g} kWh")
        with st.form("add_task"):
            minutes = st.number_input(
                "Run time (minutes)", min_value=1, max_value=1440,
                value=preset["minutes"], step=1, key=f"duration_{appliance}",
            )
            earliest, deadline = st.select_slider(
                "Available from / finish by", options=list(range(0, 1441, 15)),
                value=(8 * 60, 22 * 60), format_func=clock, key="window",
            )
            labels = {task["id"]: f"{i + 1}. {task['appliance']}" for i, task in enumerate(tasks)}
            after = st.selectbox(
                "Run after", [None] + list(labels),
                format_func=lambda value: labels.get(value, "Any time in my window"),
                key="after",
            )
            with st.expander("Adjust energy estimate"):
                kwh = st.number_input(
                    "Energy for this run (kWh)", min_value=0.001, max_value=100.0,
                    value=preset["kwh"], step=0.05, format="%.3f", key=f"energy_{appliance}",
                    help="Use the energy label or manual when available. Consumption varies by programme.",
                )
            if st.form_submit_button("Add to day", type="primary", width="stretch", key="add"):
                if minutes > deadline - earliest:
                    st.error("The run needs a wider window to finish.")
                else:
                    task = dict(id=uuid4().hex, appliance=appliance, minutes=minutes,
                                kwh=kwh, earliest=earliest, deadline=deadline,
                                after=after, status="Planned", start=None)
                    try:
                        updated, _ = plan_day(profile, tasks + [task], not_before)
                    except ValueError as error:
                        st.error(str(error))
                    else:
                        persist(updated)
        st.caption("Estimates vary by appliance and programme. Adjust them to match your run. "
                   "Adding an appliance updates pending start times.")

    with schedule:
        st.subheader(selected_date.strftime("Your %A plan"))
        if not tasks:
            st.info("Add the appliances you want to use. Your start and finish times will appear here.")
        else:
            scheduled = [task for task in tasks if task["start"] is not None]
            finished = [task for task in tasks if task["status"] == "Done"]
            progress, energy = st.columns(2)
            progress.metric("Completed", f"{len(finished)} / {len(tasks)}")
            energy.metric("Estimated task energy", f"{sum(t['kwh'] for t in tasks):.2f} kWh")
            st.progress(len(finished) / len(tasks))
            st.caption("Running and done are self-reported. Energy is estimated for the listed runs.")
            if st.button("Replan pending appliances", key="replan"):
                updated, _ = plan_day(profile, tasks, not_before)
                persist(updated)
            for task in sorted(tasks, key=lambda t: (t["start"] is None, t["start"] or 0)):
                with st.container(border=True):
                    title, action = st.columns([3, 2])
                    with title:
                        st.markdown(f"**{task['appliance']}**")
                        if task["start"] is not None:
                            st.subheader(f"{clock(task['start'])}–{clock(task['start'] + task['minutes'])}")
                        else:
                            st.warning(task.get("reason", "Choose a wider window."))
                        st.caption(f"{task['status']} · {task['minutes']} min · ~{task['kwh']:g} kWh")
                        if task["after"] in labels:
                            st.caption(f"After {labels[task['after']]}")
                    with action:
                        parent_done = (task["after"] is None or any(
                            other["id"] == task["after"] and other["status"] == "Done"
                            for other in tasks))
                        if task["status"] == "Planned" and task["start"] is not None:
                            if st.button("Start", key=f"start_{task['id']}", disabled=not parent_done):
                                task["status"] = "Running"
                                persist(tasks)
                        if task["status"] != "Done" and task["start"] is not None:
                            if st.button("Mark done", key=f"done_{task['id']}", disabled=not parent_done):
                                task["status"] = "Done"
                                persist(tasks)
                        elif task["status"] == "Done":
                            locked_child = any(other["after"] == task["id"] and other["status"] != "Planned"
                                               for other in tasks)
                            if st.button("Undo done", key=f"undo_{task['id']}", disabled=locked_child):
                                task["status"] = "Planned"
                                persist(tasks)
                        dependent = any(other["after"] == task["id"] for other in tasks)
                        if st.button("Remove", key=f"remove_{task['id']}", disabled=dependent,
                                     help="Remove dependent tasks first." if dependent else None):
                            updated, _ = plan_day(profile, [t for t in tasks if t != task], not_before)
                            persist(updated)
            rows = [{"Appliance": t["appliance"],
                     "Start": clock(t["start"]) if t["start"] is not None else "Unscheduled",
                     "Finish": clock(t["start"] + t["minutes"]) if t["start"] is not None else "",
                     "Status": t["status"], "Energy estimate (kWh)": t["kwh"]} for t in tasks]
            st.download_button("Download day plan", pd.DataFrame(rows).to_csv(index=False),
                               file_name=f"peakshift-{selected_date}.csv", mime="text/csv")
            with st.expander("See demand across your day"):
                load = [float(v) for v in profile for _ in range(60)]
                for task in scheduled:
                    add_task_load(load, task, task["start"])
                chart = pd.DataFrame({"Typical household": [v for v in profile for _ in range(60)],
                                      "With your appliance plan": load})
                chart.index = pd.to_datetime(chart.index, unit="m", origin=str(selected_date))
                st.line_chart(chart, x_label="Time", y_label="Estimated demand (kW)")
                st.caption("Sample weekday demand plus the listed tasks. Existing appliance use "
                           "may already be present in the sample. Curves estimate average run power.")

with data:
    st.subheader("Recorded household demand")
    counts = hourly["mean"].resample("D").count()
    dates = [date.date() for date in counts[counts == 24].index]
    recorded_date = st.selectbox("Recorded day", dates, index=len(dates) - 1, key="recorded_date")
    readings = hourly.loc[str(recorded_date), "mean"]
    total, peak = st.columns(2)
    total.metric("Recorded daily energy", f"{readings.sum():.2f} kWh")
    peak.metric("Highest hourly average", f"{readings.max():.2f} kW")
    readings.index = readings.index.hour
    st.line_chart(readings.rename("Recorded demand"), x_label="Hour (Swiss time)", y_label="Demand (kW)")
    st.caption("Recorded Swiss household readings, 2023–2024 · Kaiser et al. · CC BY 4.0.")
    st.markdown("[Household dataset and credit](https://zenodo.org/records/21398769)")
    with st.expander("Appliance estimates"):
        st.dataframe(pd.DataFrame([
            {"Appliance": name, "Example run (min)": p["minutes"], "Estimated kWh": p["kwh"]}
            for name, p in APPLIANCES.items()
        ]), hide_index=True, width="stretch")
        st.markdown(f"[Appliance energy reference — Power NI]({SOURCE})")
        st.caption("Example durations and energy estimates are editable. Kitchen and vacuum "
                   "estimates use reference power × example duration.")

with evidence:
    st.subheader("Recorded test results")
    st.caption("Historical benchmark. The current appliance planner has not received "
               "a new held-out evaluation.")
    report = json.loads(
        (Path(__file__).resolve().parent / "results/evaluation.json").read_text()
    )
    st.warning(
        "On the final test, hourly error improved slightly, daily peak error worsened, and model"
        " scheduling tied yesterday-based scheduling on every evaluated day."
    )
    for label, key in [
        ("Final test · September–December 2024", "test"),
        ("Validation · May–September 2024", "validation"),
    ]:
        scores = report[key]
        with st.container(border=True):
            st.subheader(label)
            st.caption(
                f"{scores['days']} complete days · {scores['hours']:,} hours · "
                f"{scores['skipped_days']} skipped days"
            )
            table = pd.DataFrame({
                "Metric": [
                    "Average hourly error (kW)",
                    "Average daily peak error (kW)",
                    "Average peak after scheduling (kW)",
                ],
                "Yesterday baseline": [
                    scores["baseline_hourly_mae_kw"],
                    scores["baseline_peak_mae_kw"],
                    scores["average_simulated_peak_kw"]["Baseline"],
                ],
                "Model": [
                    scores["model_hourly_mae_kw"],
                    scores["model_peak_mae_kw"],
                    scores["average_simulated_peak_kw"]["Model"],
                ],
            })
            st.dataframe(table.round(3), hide_index=True, width="stretch")
            for reference, title in [
                ("original", "original 18:00 start"),
                ("baseline", "yesterday-based schedule"),
            ]:
                outcomes = scores[f"model_vs_{reference}"]
                st.write(
                    f"Against the {title}: **{outcomes['better']} better · "
                    f"{outcomes['equal']} equal · {outcomes['worse']} worse**."
                )
            if scores["skipped_dates"]:
                st.caption(
                    "Skipped: " + ", ".join(scores["skipped_dates"])
                    + " (25-hour clock-change day)."
                )
    st.caption(
        "Lower errors and peaks are better. Benchmark settings: 1 kW for one hour, allowed "
        "18:00–22:00, original start 18:00. Changing task controls does not change these frozen "
        "results."
    )
    st.download_button(
        "Download evaluation results", json.dumps(report, indent=2),
        file_name="peakshift-evaluation.json", mime="application/json",
    )

