# PeakShift

Plan and track appliance use throughout a day. Choose an appliance, run time, and allowed window. PeakShift schedules runs together and supports tasks such as drying after washing. Plans and completion status are saved in each visitor's browser.

Demand estimates use one Swiss household. Presets are editable estimates. All plan times follow Europe/Zurich. The app has **Your day**, **Household data**, and **What the tests showed** tabs.

## GitHub Pages version

The website runs the Python daily scheduler through Pyodide, with plans saved in each visitor's browser. It exports the sample household data during the build. GitHub Actions builds and publishes it from `main` once Pages is enabled.

Build the static site locally with `python build_site.py`. Generated files go into the ignored `_site/` folder. The first browser visit downloads the Python runtime.

## Build and preview the website

Use Python 3.11. From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python build_site.py
python -m http.server 8000 --directory _site
```

Open http://localhost:8000 in your browser. If `.venv` already exists, start at the activation command. The household used for the experiment is bundled as a 375 KB compressed CSV, so no external data download or API key is needed.

Select a planning date and add appliances. Use **Run after** to link tasks, **Start** and **Mark done** to track them, and **Replan pending appliances** to update remaining starts. Adding a run reschedules pending tasks. Running/completed tasks retain their times. A same-appliance run cannot overlap another run of that appliance. Tasks that cannot fit remain visibly unscheduled. Plans are saved per browser and device. Clearing site data removes saved plans. CSV exports include unscheduled tasks.

Editable appliance defaults are in `appliances.py`, based on [Power NI's appliance guide](https://powerni.co.uk/help/energy-guides/which-appliances-use-the-most-electricity/). Durations are example runs; cooking, kettle, and vacuum energy estimates use reference power multiplied by run time. Actual consumption varies by programme, load, and model. The original test results remain available, including the weak final-test results. Those scores do not evaluate the new daily planner.

## Weekday planner

For every weekday and hour, average available readings from 1 January 2023–25 May 2024, the original training dates. For example, Monday at 18:00 uses past Mondays at 18:00. The planner uses no validation or final-test dates to fit these averages. Each weekday has a 24-hour profile.

The daily planner tries quarter-hour starts for each run, prioritizing narrower windows. It includes already-placed loads and dependencies. It chooses a lower daily peak, then a lower sum of squared demand across the day to spread overlapping loads, then an earlier start. This greedy procedure does not guarantee a globally optimal plan. Runs use constant estimated average power; the hourly background is held constant within each hour. Total task energy is conserved. Existing appliance loads may already be present in the historical household background. A larger peak elsewhere in the day can leave every candidate's daily peak equal. Averages smooth out unusual appliance use and seasons. A recommendation for a specific future date needs recent household data and further evaluation.

## Original experiment

1. Convert 15-minute energy readings from kWh into average power in kW, then calculate hourly averages. Incomplete hours remain missing.
2. Train a small decision tree using demand 24 and 168 hours earlier, the hour, and the weekday. Split dates chronologically: the first 70% for training, the next 15% for validation, and the last 15% for final testing. The first week (1–7 January 2023) supplies lag history, not training targets; eligible training targets begin on 8 January.
3. Add the hypothetical task to each allowed hour of the forecast and choose the lowest resulting daily peak. Ties use the earliest start.
4. Add the same task to the actual measurements afterward to check the decision. Actual target demand is not an input to the model or scheduler.

The model uses `absolute_error`, `max_depth=5`, and `random_state=42`. These settings were fixed before final testing. The command-line evaluation retains the decision tree and original earliest-start tie rule. The daily planner uses weekday averages and the squared-demand tie rule described above. The new planner has not received a new held-out evaluation.

## Results

Lower error is better. MAE means mean absolute error: the average size of a prediction's mistake.

| Metric | Validation baseline | Validation model | Final baseline | Final model |
|---|---:|---:|---:|---:|
| Hourly MAE (kW) | 0.564 | 0.453 | 0.807 | 0.781 |
| Daily peak MAE (kW) | 2.998 | 2.487 | 2.272 | 2.604 |
| Average simulated daily peak after scheduling (kW) | 4.894 | 4.715 | 12.141 | 12.141 |

Validation: 110 days / 2,640 hours, 26 May–12 September 2024. Final test: 109 complete days / 2,616 hours, 13 September–31 December 2024; the 25-hour day on 27 October was skipped for both methods.

**The final result is mixed.** Hourly error improved slightly, daily peak error worsened, and model scheduling tied yesterday-based scheduling on all 109 final-test days. Validation scheduling was better on 20 days, equal on 89, and worse on 1 compared with the baseline scheduler. We cannot claim a final-test scheduling advantage.

The benchmark assumes an additional 1 kW task lasting one hour, allowed between 18:00 and 22:00, originally starting at 18:00. App controls allow other task settings; they do not change the saved benchmark results. Reduced simulated peak demand does not establish reduced energy use, bills, or carbon emissions.

## Reproduce the benchmark

```bash
python train.py
python explore.py
```

`train.py` reproduces both evaluation periods and writes JSON/CSV results into `results/`. It does not open plot windows. `explore.py` displays the household history.

| File | Responsibility |
|---|---|
| `web/app.js` | Website controls, browser storage, charts, and connection to the Python planner |
| `build_site.py` | Export sample data and build the static website |
| `explore.py` | Load and convert the household readings |
| `forecast.py` | Original decision-tree experiment and training-only weekday profiles |
| `scheduler.py` | Original one-hour experiment scheduler |
| `daily_planner.py` | Schedule variable-duration runs together |
| `appliances.py` | Editable appliance energy and duration presets |
| `evaluation.py` | Score forecasts and simulated scheduling decisions |
| `train.py` | Run and save the experiment |

## Data and credits

[Dataset on residential electricity load profiles in Switzerland](https://zenodo.org/records/21398769), by Katharina Kaiser, Markus Kreft, Marina González Vayá, and Gabriela Hug. Version v1, DOI [10.5281/zenodo.21398769](https://doi.org/10.5281/zenodo.21398769), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Description paper](https://arxiv.org/abs/2607.19294). The bundled file is the original meter 133930 CSV, gzip-compressed without changing its contents. See [data notes](data/README.md) for selection and units.

Built with [pandas](https://pandas.pydata.org/), [scikit-learn](https://scikit-learn.org/), [Matplotlib](https://matplotlib.org/), and [Pyodide](https://pyodide.org/). OpenAI Codex/ChatGPT assisted with planning, code generation, debugging, tests, UI, and documentation. The student is reviewing and learning the implementation before submission. shadcn and pick-ui-library guidance was reviewed for UI choices; no React/shadcn packages were installed.
