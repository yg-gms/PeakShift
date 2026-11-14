import pandas as pd

from scheduler import choose_start


def evaluate_period(comparison):
    counts = comparison.resample("D").count()
    complete_days = counts.index[(counts == 24).all(axis=1)]
    readings = comparison.loc[comparison.index.normalize().isin(complete_days)]
    assert not readings.empty, "No complete 24-hour days to evaluate."

    peaks = readings.resample("D").max().dropna()
    scores = {
        "days": len(complete_days),
        "hours": len(readings),
        "skipped_days": len(counts) - len(complete_days),
        "skipped_dates": [str(date.date()) for date in counts.index.difference(complete_days)],
        "baseline_hourly_mae_kw": float((readings["mean"] - readings["yesterday"]).abs().mean()),
        "model_hourly_mae_kw": float((readings["mean"] - readings["model"]).abs().mean()),
        "baseline_peak_mae_kw": float((peaks["mean"] - peaks["yesterday"]).abs().mean()),
        "model_peak_mae_kw": float((peaks["mean"] - peaks["model"]).abs().mean()),
    }

    rows = []
    for date, day in readings.groupby(readings.index.normalize()):
        starts = {
            "Original": day.index[day.index.hour == 18][0],
            "Baseline": choose_start(day["yesterday"])[0],
            "Model": choose_start(day["model"])[0],
        }
        result = {"date": date}
        for name, start in starts.items():
            actual = day["mean"].copy()
            actual.loc[start] += 1.0
            result[name] = actual.max()
        rows.append(result)
    return scores, pd.DataFrame(rows).set_index("date")
