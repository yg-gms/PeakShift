import tempfile
import unittest
from pathlib import Path

import pandas as pd

import explore


class SwissHourlyTests(unittest.TestCase):
    def load(self, timestamps, energy):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "meter.csv"
            pd.DataFrame(
                {"timestamp_utc": timestamps, "kWh_to_installation": energy}
            ).to_csv(path, sep=";", index=False)
            return explore.load_hourly(path)

    def test_interval_energy_becomes_hourly_average_power_in_swiss_time(self):
        times = pd.date_range("2023-01-01", periods=4, freq="15min", tz="UTC")
        hourly = self.load(times, [0.25, 0.5, 0.75, 1.0])
        self.assertAlmostEqual(hourly["mean"].iloc[0], 2.5)
        self.assertEqual(hourly["count"].iloc[0], 4)
        self.assertEqual(str(hourly.index[0]), "2023-01-01 01:00:00+01:00")

    def test_missing_intervals_and_whole_hours_stay_missing(self):
        times = pd.date_range("2023-01-01", periods=12, freq="15min", tz="UTC")
        hourly = self.load(times[[0, 1, 3, 8, 9, 10, 11]], [0.25] * 7)
        self.assertEqual(hourly["count"].tolist(), [3, 0, 4])
        self.assertTrue(hourly["mean"].iloc[:2].isna().all())
        self.assertEqual(hourly["mean"].iloc[2], 1.0)

    def test_daylight_saving_repeated_hour_keeps_both_instants(self):
        times = pd.date_range("2023-10-29", periods=8, freq="15min", tz="UTC")
        hourly = self.load(times, [0.25] * 8)
        self.assertEqual(hourly["mean"].tolist(), [1.0, 1.0])
        self.assertEqual(hourly.index.hour.tolist(), [2, 2])
        self.assertEqual(
            [stamp.utcoffset().total_seconds() for stamp in hourly.index],
            [7200, 3600],
        )


if __name__ == "__main__":
    unittest.main()
