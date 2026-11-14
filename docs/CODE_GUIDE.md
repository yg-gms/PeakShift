# PeakShift code and forecasting guide

PeakShift has two interfaces. `app.py` runs the local Streamlit app. The GitHub Pages interface runs in the browser. Both use `daily_planner.py` for scheduling. The public interface saves plans in the visitor's browser; the Streamlit interface saves plans in a local SQLite database.

## Every code file

| File | What it does |
|---|---|
| `explore.py` | Reads the bundled household CSV, converts interval energy to hourly average power, preserves missing readings and clock-change hours, and optionally plots the household history. |
| `forecast.py` | Builds the current weekday averages and reproduces the original decision-tree forecast. Both fit their estimates using the earlier training dates. |
| `appliances.py` | Holds the eight editable appliance presets and the reference link. Each preset has an example duration in minutes and energy in kWh. |
| `daily_planner.py` | Validates tasks, tries possible start times, coordinates multiple appliances and dependencies, preserves running/completed tasks, and returns the schedule and estimated demand curve. `add_task_load()` is also used to draw the same estimated loads. |
| `plan_store.py` | Loads and saves dated plans for the local Streamlit installation. SQLite transactions and revision checks prevent a stale browser tab from overwriting a newer save. |
| `app.py` | Provides the Streamlit controls, scheduling cards, progress actions, CSV download, household readings, and benchmark results. It delegates calculations and storage to the other modules. |
| `scheduler.py` | Reproduces the original fixed one-hour experiment. It tries each allowed hour and chooses the lowest predicted whole-day peak. Equal peaks use the earliest start. |
| `evaluation.py` | Scores the original forecasts and simulated schedules on complete 24-hour days. It calculates hourly error, daily peak error, and actual-background peaks after adding the task. |
| `train.py` | Runs the original experiment with its fixed settings and writes the JSON/CSV benchmark files in `results/`. It reports validation and final-test results, including failures. |
| `build_site.py` | Builds `_site/` for GitHub Pages. It exports the weekday profiles, complete recorded days, appliance presets, and frozen results into JSON, and copies the web interface and shared Python scheduler. It excludes saved personal plans. |
| `web/index.html` | Defines the browser interface, labelled inputs, views, chart canvases, and accessible status messages. |
| `web/style.css` | Controls typography, colour, cards, focus indicators, charts, and the responsive phone/desktop layout. |
| `web/app.js` | Connects the browser controls to the shared Python scheduler through Pyodide. It handles browser-local storage, progress updates, CSV download, charts, and displaying exported readings/results. It passes task data as JSON rather than executable code. |
| `.github/workflows/pages.yml` | Builds and publishes the static site when `main` changes or the workflow is run manually. GitHub Pages serves the generated files. |

`requirements.txt` pins Python dependencies. `.streamlit/config.toml` sets the local app theme. `.gitignore` excludes raw downloads, virtual environments, caches, saved local plans, and generated site output. The documents contain the write-up, appliance references, and this explanation.

## The units and source data

The source is imported electricity for one Swiss household in 2023–2024. Each row contains energy for a 15-minute interval.

- **kWh** measures energy over time, such as the total for a wash.
- **kW** measures power, such as household demand at an hour.

`load_hourly()` divides each quarter-hour energy value by 0.25 hours to get average kW, then averages four readings to produce an hourly value. Four readings of 0.25 kWh each represent 1 kWh over the hour and an hourly average of 1 kW. Incomplete hours remain missing.

Aggregation happens in UTC before converting labels to Europe/Zurich. This preserves both occurrences of the repeated autumn clock hour. Complete-day comparisons exclude days with 23 or 25 hourly readings. The public data view contains 727 complete recorded days.

## The forecast used by the current planner

The current planner uses a **weekday/hour average**. This is a statistical forecast fitted from past readings.

For a Monday at 18:00, take every available Monday 18:00 reading in the training period, add them together, and divide by the number of readings. Repeat for all 24 hours and all seven weekdays. The result is 168 average values.

The training dates are 1 January 2023–25 May 2024. Validation and final-test dates are excluded from fitting these averages. A future date chooses the corresponding weekday's profile. The profile describes a typical day in the sample household; it does not use current weather, holidays, a specific household's recent readings, or the user's actual appliance measurements.

Averaging makes this forecast easy to explain and stable, but it smooths out unusual peaks and seasonal differences. Two Mondays with very different behaviour still receive the same typical Monday estimate.

## The original decision-tree model

The saved benchmark evaluates a separate decision tree. The current product no longer uses that tree to generate its weekday plans.

### Inputs and target

Each eligible hour becomes one training row with four inputs:

1. Demand 24 elapsed hours earlier (`yesterday`).
2. Demand 168 elapsed hours earlier (`last_week`).
3. Hour of the day, from 0 to 23.
4. Weekday, from 0 for Monday to 6 for Sunday.

The target is the household's actual hourly average demand in kW. Target-hour demand is excluded from the input features. At clock changes, elapsed-hour lags can differ from the same local clock hour on the earlier date.

The first week supplies lag history. Its rows lack a complete 168-hour lag and are dropped before fitting. Eligible training targets begin on 8 January 2023.

### Chronological split

The code takes all local dates in order. The first 70% define training dates, the next 15% validation, and the final 15% testing.

- Training targets end on 25 May 2024.
- Validation runs from 26 May to 12 September 2024.
- The final test runs from 13 September to 31 December 2024.

The code fits the tree once on training rows. It predicts later rows using their available historical lag readings, without fitting again on validation or test targets. This is an hourly historical evaluation with observed lags, rather than a recursive forecast of an entire unknown future season.

### What the tree learns

The model is `DecisionTreeRegressor(criterion="absolute_error", max_depth=5, random_state=42)`.

During training, it tries threshold questions about the inputs, such as whether yesterday's demand is below a particular value. Each split divides training rows into two groups. The absolute-error criterion favours splits that reduce absolute prediction errors. A terminal group, or leaf, predicts the median training target in that group.

A depth limit of five permits at most five decisions along a path and at most 32 leaves. The implementation can use fewer leaves. The seed makes its randomized choices repeatable. Different inputs that reach the same leaf receive the same prediction, which can produce flat forecast sections.

The hour and weekday are numeric inputs. This tree does not explicitly encode that Sunday and Monday are adjacent, or that 23:00 and 00:00 are adjacent. It also has no weather or appliance-state inputs.

### Baseline and scoring

The baseline forecast repeats demand from 24 hours earlier. Hourly MAE is the average absolute difference between predicted and actual hourly power. Daily peak MAE compares each forecast's highest hourly value with the actual day's highest hourly value.

The original scheduling benchmark adds an extra 1 kW task for one hour. Starts are allowed at 18:00, 19:00, 20:00, or 21:00. It first chooses using the forecast, then adds the task to measured background demand to score the decision. It compares model scheduling, baseline scheduling, and an original 18:00 start.

The fixed final test showed hourly MAE changing from **0.807 to 0.781 kW**, daily peak MAE changing from **2.272 to 2.604 kW**, and scheduling tying the baseline on **all 109 evaluated days**. The model improved hourly error slightly, worsened peak error, and established no final-test scheduling advantage. The 25-hour day on 27 October was excluded.

These scores describe the original experiment. They do not validate the current multi-appliance planner. The final period has already been examined, so changes informed by it require a genuinely new unseen evaluation.

## How the daily scheduler works

The scheduler receives the selected weekday's 24-hour profile and a list of appliance runs. Each task has an ID, appliance name, duration, estimated kWh, allowed window, optional earlier task, status, and scheduled start.

1. Check the profile and task constraints. Copy the task list so scheduling does not unexpectedly mutate its caller's data.
2. Expand each hourly background estimate into 60 equal minute values. This supplies a calculation grid and adds no new measured detail.
3. Add running and completed tasks at their existing starts.
4. Consider ready pending tasks, prioritizing the tightest window relative to duration, then higher-energy runs. A dependency becomes ready after its earlier task has been considered.
5. Try starts every 15 minutes within the allowed window. On the current day, new starts follow the current Swiss time. A task must finish before its deadline and after its prerequisite. Two runs of the same appliance cannot overlap.
6. Add each candidate's load and compare the whole-day peak. For equal peaks, prefer the smaller sum of squared demand across the day, which discourages concentrating loads together. If still equal, prefer the earlier start.
7. Keep that placement and include its load when placing subsequent tasks. A run that cannot fit stays visibly unscheduled with a reason.

For a run using 1.2 kWh over 60 minutes, the added average power is `1.2 × 60 / 60 = 1.2 kW`. A three-minute kettle run using 0.135 kWh adds `0.135 × 60 / 3 = 2.7 kW` for those three minutes. This conserves energy while assuming constant power throughout each run.

The procedure is greedy. It chooses each placement using the tasks already placed and does not search every combination for a global optimum. Appliance cycle spikes and human use can differ from these average estimates. Historical demand can already include appliance activity, so the listed tasks are additional hypothetical loads on that background.

A larger morning peak can also make every evening candidate's whole-day peak identical. The secondary score can still favour a quieter task hour, while the estimated daily peak reduction remains zero.

## Browser hosting and saved plans

GitHub Pages serves static files and cannot run the Streamlit server. Pyodide loads Python in the browser and executes the published copy of `daily_planner.py`. The profiles and historical readings are exported at build time. The website does not train a decision tree on each visit.

Each visitor's plans are saved in browser local storage, separate from the local Streamlit SQLite database. A page refresh preserves them. Clearing site data, using another browser/device, or using temporary private browsing storage can remove or separate them. CSV download provides a portable record. The initial Python runtime download needs an internet connection.

The Pages build contains the public sample data, preset estimates, and frozen results. It excludes `data/plans.sqlite3` and the ignored raw download. If the repository is made public, its source and committed history are also public.

## Next steps

1. Walk through the implementation and explain one complete plan, from weekday average through task placement and saved status.
2. Check the appliance presets against labels and programmes available in the intended household. Replace example values when better measurements exist.
3. Ask a few users to add a wash, link a dryer, change a window, and mark completion. Record where they hesitate.
4. Collect recent readings from the intended household and reserve genuinely unseen future dates. Evaluate the weekday forecast and multi-appliance decisions with fixed settings before claiming improvements.
5. Consider more elaborate scheduling only if observed failures justify it. A useful example would be a feasible combination that the greedy procedure misses.
6. For submission, review the mixed benchmark result and assistance disclosure, complete the team details, record the demo, and verify public links.

## References

- [GitHub Pages publishing and supported content](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Pyodide browser Python runtime](https://pyodide.org/en/stable/usage/quickstart.html)
- [scikit-learn decision-tree regressor](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html)
- Dataset and appliance citations are in `README.md`, `data/README.md`, and `docs/APPLIANCE_PRESETS.md`.
