from explore import DATA_FOLDER, METER_ID, load_hourly
from sklearn.tree import DecisionTreeRegressor
import matplotlib.pyplot as plt
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

predictions = model.predict(validation[features])

model_mae = (validation["mean"] - predictions).abs().mean()
baseline_mae = (
    validation["mean"] - validation["yesterday"]
).abs().mean()

print(f"Baseline MAE: {baseline_mae:.3f} kW")
print(f"Decision tree MAE: {model_mae:.3f} kW")

comparison = validation[["mean", "yesterday"]].copy()

comparison["model"] = predictions

daily_peaks = comparison.resample("D").max()

baseline_peak_mae = (
    daily_peaks["mean"] - daily_peaks["yesterday"]
).abs().mean()

model_peak_mae = (
    daily_peaks["mean"] - daily_peaks["model"]
).abs().mean()

print(f"Baseline daily peak MAE: {baseline_peak_mae:.3f} kW")
print(f"Model daily peak MAE: {model_peak_mae:.3f} kW")

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
