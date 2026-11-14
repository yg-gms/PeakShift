import unittest

import pandas as pd

from evaluation import evaluate_period


class EvaluationTests(unittest.TestCase):
    def test_scores_same_complete_days_and_uses_forecasts_for_choices(self):
        times = pd.date_range("2024-10-26", "2024-10-28", freq="h", inclusive="left", tz="Europe/Zurich")
        data = pd.DataFrame({"mean": 1.0, "yesterday": 1.0, "model": 1.0}, index=times)
        data.loc[times[18], ["mean", "model"]] = 4.0
        data.loc[data.index.day == 27, "mean"] = 100.0
        original = data.copy()

        scores, schedules = evaluate_period(data)

        self.assertEqual(scores["days"], 1)
        self.assertEqual(scores["hours"], 24)
        self.assertEqual(scores["skipped_days"], 1)
        self.assertAlmostEqual(scores["baseline_hourly_mae_kw"], 0.125)
        self.assertEqual(scores["model_hourly_mae_kw"], 0.0)
        self.assertEqual(scores["baseline_peak_mae_kw"], 3.0)
        self.assertEqual(schedules["Original"].iloc[0], 5.0)
        self.assertEqual(schedules["Baseline"].iloc[0], 5.0)
        self.assertEqual(schedules["Model"].iloc[0], 4.0)
        pd.testing.assert_frame_equal(data, original)


if __name__ == "__main__":
    unittest.main()
