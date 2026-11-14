from explore import DATA_FOLDER, METER_ID, load_hourly
from sklearn.tree import DecisionTreeRegressor

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