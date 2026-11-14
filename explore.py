from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


DATA_FOLDER = Path(__file__).resolve().parent / "data/raw/swiss"
METER_ID = 133930


def load_hourly(path):
    data = pd.read_csv(
        path,
        sep=";",
        encoding="utf-8-sig",
        usecols=["timestamp_utc", "kWh_to_installation"],
    )
    data["timestamp"] = pd.to_datetime(data["timestamp_utc"], utc=True)
    data = data.set_index("timestamp").sort_index()

    # shortcut: expects the verified Swiss files; validate any new data source first.
    energy = data["kWh_to_installation"]

    # The source is kWh per 15-minute interval; divide by 0.25 hours for kW.
    demand = energy.asfreq("15min") / 0.25
    hourly = demand.resample("h").agg(["mean", "count"])
    hourly.loc[hourly["count"] < 4, "mean"] = float("nan")
    # Aggregate in UTC so the repeated autumn clock hour stays distinct.
    hourly.index = hourly.index.tz_convert("Europe/Zurich")
    return hourly


if __name__ == "__main__":
    hourly = load_hourly(DATA_FOLDER / "smart_meter_data" / f"{METER_ID}.csv")

    print("Swiss household meter:", METER_ID)
    print("First hour:", hourly.index.min())
    print("Last hour:", hourly.index.max())
    print("Total hours:", len(hourly))
    print("Incomplete hours:", hourly["mean"].isna().sum())
    print(hourly.head())

    hourly["mean"].plot(
        figsize=(12, 4),
        title=f"Swiss household {METER_ID}: hourly average electricity demand",
        xlabel="Date (Swiss local time)",
        ylabel="Average imported demand (kW)",
    )

    plt.tight_layout()
    plt.show()
