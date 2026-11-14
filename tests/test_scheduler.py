import unittest

import pandas as pd

from scheduler import choose_start


class SchedulerTests(unittest.TestCase):
    def test_compares_whole_day_peaks_and_breaks_ties_by_earliest_start(self):
        times = pd.date_range("2024-05-26", periods=24, freq="h", tz="Europe/Zurich")
        forecast = pd.Series(1.0, index=times)
        forecast.iloc[[12, 18, 19, 20, 21]] = [5.0, 4.8, 3.0, 2.0, 0.2]
        original = forecast.copy()

        start, peaks = choose_start(forecast)

        self.assertEqual(start, times[19])
        self.assertEqual(list(peaks), list(times[18:22]))
        self.assertAlmostEqual(peaks[times[18]], 5.8)
        self.assertEqual(list(peaks.values())[1:], [5.0, 5.0, 5.0])
        pd.testing.assert_series_equal(forecast, original)

    def test_requires_a_complete_forecast_before_recommending(self):
        times = pd.date_range("2024-05-26", periods=24, freq="h", tz="Europe/Zurich")
        forecast = pd.Series(1.0, index=times)
        with self.assertRaises(AssertionError):
            choose_start(forecast.iloc[:-1])
        forecast.iloc[12] = float("nan")
        with self.assertRaises(AssertionError):
            choose_start(forecast)


if __name__ == "__main__":
    unittest.main()
