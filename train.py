from explore import DATA_FOLDER, METER_ID, load_hourly
from sklearn.tree import DecisionTreeRegressor
import matplotlib.pyplot as plt
from pathlib import Path
import json
from evaluation import evaluate_period
from scheduler import choose_start

hourly = load_hourly(
    DATA_FOLDER / "smart_meter_data" / f"{METER_ID}.csv"
)

hourly["yesterday"] = hourly["mean"].shift(24)
hourly["last_week"] = hourly["mean"].shift(168)
hourly["hour"] = hourly.index.hour
hourly["weekday"] = hourly.index.day_of_week

features = ["yesterday", "last_week", "hour", "weekday"]

training_table = hourly[features + ["mean"]].dropna()

days = hourly.index.normalize().unique()
validation_start = days[int(len(days) * 0.70)]
test_start = days[int(len(days) * 0.85)]

train = training_table.loc[
    training_table.index < validation_start
]

validation = training_table.loc[
    (training_table.index >= validation_start)
    & (training_table.index < test_start)
]

assert train.index.max() < validation.index.min()

model = DecisionTreeRegressor(
    criterion="absolute_error",
    max_depth=5,
    random_state=42,
)
model.fit(train[features], train["mean"])

results_folder = Path(__file__).resolve().parent / "results"
results_folder.mkdir(exist_ok=True)
report = {}

for name, period in {
    "validation": validation,
    "test": training_table.loc[training_table.index >= test_start],
}.items():
    comparison = period[["mean", "yesterday"]].copy()
    comparison["model"] = model.predict(period[features])
    scores, schedules = evaluate_period(comparison)
    report[name] = scores
    schedules.to_csv(results_folder / f"{name}-scheduling.csv")
    print(f"{name.upper()}: {scores['days']} days, {scores['hours']} hours; "
          f"{scores['skipped_days']} skipped days {scores['skipped_dates']}")
    print(f"Hourly MAE: baseline {scores['baseline_hourly_mae_kw']:.3f}, "
          f"model {scores['model_hourly_mae_kw']:.3f} kW")
    print(f"Daily peak MAE: baseline {scores['baseline_peak_mae_kw']:.3f}, "
          f"model {scores['model_peak_mae_kw']:.3f} kW")
    print("Average simulated daily peaks (kW):")
    print(schedules.mean().round(3))
    for reference in ["Original", "Baseline"]:
        reduction = (schedules[reference] - schedules["Model"]).round(9)
        outcomes = {
            "better": int((reduction > 0).sum()),
            "equal": int((reduction == 0).sum()),
            "worse": int((reduction < 0).sum()),
        }
        scores[f"model_vs_{reference.lower()}"] = outcomes
        print(f"Model vs {reference}: {outcomes}")
    scores["average_simulated_peak_kw"] = schedules.mean().to_dict()
    if name == "validation":
        validation_comparison = comparison

report["model"] = {"meter_id": METER_ID, "criterion": "absolute_error", "max_depth": 5, "random_state": 42}
report["validation_start"] = str(validation_start)
report["test_start"] = str(test_start)
(results_folder / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
comparison = validation_comparison

# Use the first validation day, chosen before inspecting scheduling results.
day = comparison.loc[str(validation_start.date())]
recommended_start, predicted_peaks = choose_start(day["model"])
original_start = day.index[day.index.hour == 18][0]

scheduled = day[["mean"]].rename(columns={"mean": "Measured background"})
scheduled["Original task"] = day["mean"]
scheduled["Recommended task"] = day["mean"]
scheduled.loc[original_start, "Original task"] += 1.0
scheduled.loc[recommended_start, "Recommended task"] += 1.0

print("Scheduling example:", validation_start.date())
print("Simulated task: 1 kW for one hour, between 18:00 and 22:00")
for start, peak in predicted_peaks.items():
    print(f"Start {start:%H:%M}: predicted whole-day peak {peak:.3f} kW")
print(f"Recommended start: {recommended_start:%H:%M}")
original_peak = scheduled["Original task"].max()
recommended_peak = scheduled["Recommended task"].max()
print(f"Simulated peak with original start: {original_peak:.3f} kW")
print(f"Simulated peak with recommended start: {recommended_peak:.3f} kW")
print(f"Simulated peak reduction: {original_peak - recommended_peak:.3f} kW")

scheduled.plot(
    figsize=(12, 4),
    title=f"One-hour task on {validation_start.date()}: original vs recommended",
    xlabel="Date (Swiss local time)",
    ylabel="Demand (kW)",
)
plt.tight_layout()

comparison.iloc[:168].plot(
    figsize=(12, 4),
    title="First validation week: actual, baseline, and model",
    xlabel="Date",
    ylabel="Demand (kW)",
)

plt.tight_layout()
plt.show()
