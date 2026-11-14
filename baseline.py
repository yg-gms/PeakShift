from explore import DATA_FOLDER, METER_ID, load_hourly

hourly = load_hourly(
    DATA_FOLDER / "smart_meter_data" / f"{METER_ID}.csv"
)

hourly["baseline"] = hourly["mean"].shift(24)

days = hourly.index.normalize().unique()
validation_start = days[int(len(days) * 0.70)]
test_start = days[int(len(days) * 0.85)]

validation = hourly.loc[
    (hourly.index >= validation_start)
    & (hourly.index < test_start)
].dropna(subset=["mean", "baseline"])

assert not validation.empty, "No valid hours to evaluate."

errors = validation["mean"] - validation["baseline"]
mae = errors.abs().mean()

print("Validation starts:", validation_start)
print("Final test starts:", test_start)
print("Hours evaluated:", len(validation))
print(f"Baseline MAE: {mae:.3f} kW")