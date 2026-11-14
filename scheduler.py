from math import isfinite


def choose_start(forecast, power_kw=1.0, earliest=18, deadline=22):
    """Choose a start for one one-hour task; a deadline of 22 means finish by 22:00."""
    if not isfinite(power_kw) or power_kw <= 0:
        raise ValueError("Task power must be a positive number.")
    if not 0 <= earliest < deadline <= 24:
        raise ValueError("Choose a window of at least one hour within the day.")
    # shortcut: support 23/25-hour clock-change days when expanding the demo.
    if len(forecast) != 24 or forecast.isna().any():
        raise ValueError("Choose a complete 24-hour day of forecasts.")

    peaks = {}
    starts = forecast.index[(forecast.index.hour >= earliest) & (forecast.index.hour < deadline)]
    for start in starts.sort_values():
        combined = forecast.copy()
        combined.loc[start] += power_kw
        peaks[start] = combined.max()

    return min(peaks, key=peaks.get), peaks
