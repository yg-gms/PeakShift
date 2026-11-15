from sklearn.tree import DecisionTreeRegressor

from explore import DATA_FILE, load_hourly


FEATURES = ["yesterday", "last_week", "hour", "weekday"]
MODEL_SETTINGS = {"criterion": "absolute_error", "max_depth": 5, "random_state": 42}


def build_forecasts():
    hourly = load_hourly(DATA_FILE)
    # Use past readings as inputs: 24 hours ago and 168 hours (one week) ago.
    hourly["yesterday"] = hourly["mean"].shift(24)
    hourly["last_week"] = hourly["mean"].shift(168)
    hourly["hour"] = hourly.index.hour
    hourly["weekday"] = hourly.index.day_of_week
    table = hourly[FEATURES + ["mean"]].dropna()

    # Split dates in order: 70% training, 15% validation, 15% final test.
    days = hourly.index.normalize().unique()
    validation_start = days[int(len(days) * 0.70)]
    test_start = days[int(len(days) * 0.85)]
    train = table.loc[table.index < validation_start]
    later = table.loc[table.index >= validation_start]

    model = DecisionTreeRegressor(**MODEL_SETTINGS)
    model.fit(train[FEATURES], train["mean"])
    comparison = later[["mean", "yesterday"]].copy()
    comparison["model"] = model.predict(later[FEATURES])
    return comparison, validation_start, test_start


def build_weekday_profiles(hourly):
    """Average each weekday/hour using only the original training dates."""
    days = hourly.index.normalize().unique()
    validation_start = days[int(len(days) * 0.70)]
    training = hourly.loc[hourly.index < validation_start, "mean"]
    # Each weekday/hour gets its average demand from the training period.
    return training.groupby([training.index.day_of_week, training.index.hour]).mean()
