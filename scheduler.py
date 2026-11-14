def choose_start(forecast):
    """Schedule an assumed 1 kW, one-hour task between 18:00 and 22:00."""
    # shortcut: this demo expects a complete 24-hour day; support 23/25-hour clock-change days when expanding the demo.
    assert len(forecast) == 24 and forecast.notna().all(), "Need a complete day of forecasts."

    peaks = {}
    starts = forecast.index[(forecast.index.hour >= 18) & (forecast.index.hour < 22)]
    for start in starts:
        combined = forecast.copy()
        combined.loc[start] += 1.0
        peaks[start] = combined.max()

    return min(peaks, key=peaks.get), peaks
